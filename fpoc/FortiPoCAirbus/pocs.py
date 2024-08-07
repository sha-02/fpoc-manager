from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import copy

import fpoc
from fpoc import FortiGate, LXC
from fpoc.FortiPoCAirbus import FortiPoCAirbus
from fpoc.typing import TypePoC
import typing

import ipaddress


def airbus(request: WSGIRequest) -> HttpResponse:
    """
    Dual-Region WEST/EAST
    WEST: Dual DC, Two Branches
    EAST: Single DC, One Branch
    """

    def compatiblize(segments: dict):
        # Restore the previous structure of the 'segments' to avoid having to change the jinja templates
        # add 'mask' and 'subnet'
        # change 'ip' from '10.10.10.1/24' to '10.10.10.1'
        for name, device_segments in segments.items():
            for seg in device_segments.values():
                seg['subnet'] = str(ipaddress.ip_interface(seg['ip']).network.network_address)
                seg['mask'] = str(ipaddress.ip_interface(seg['ip']).netmask)
                seg['ip'] = str(ipaddress.ip_interface(seg['ip']).ip)

    # def lan_segment(segments: dict):
    #     return {'port': 'port5', **segments['LAN']}
    def lan_segment(devname: str, poc: TypePoC, segments: dict):
        return {'port': poc.devices[devname].lan.port, **segments[devname]['LAN']}

    def vrf_segments(segments: dict, ctxt: dict):
        if not ctxt['vrf_aware_overlay']:
            return {}

        return segments

    def lxc_context(lxc_name: str, segments_devices: dict, context: dict):
        segments = segments_devices[lxc_name]

        base_segment = {'ipmask': segments['LAN']['ip_lxc'] + '/' + segments['LAN']['mask'],
                        'gateway': segments['LAN']['ip']}

        # Construct the list of all LXCs with their IPs to populate the /etc/hosts of each LXC
        hosts = []
        for name, segs in segments_devices.items():
            if not context['vrf_aware_overlay']:
                new_name = f"PC-{name}".replace("_", "-").replace("LAN-", "")
                hosts.append({'name': new_name, 'ip': segs['LAN']['ip_lxc']})
            else:
                for seg in segs.values():
                    new_name = f"PC-{name}-{seg['alias']}".replace("_", "-").replace("LAN-", "").upper()
                    hosts.append({'name': new_name, 'ip': seg['ip_lxc']})

        if not context['vrf_aware_overlay']:
            return { **base_segment, 'hosts': hosts }

        # Add 'gw' (ip@ of FGT) and mask for convenience in the lxc rendering file
        vrf_segs = copy.deepcopy(vrf_segments(segments, context))
        vrf_segs.pop('port5', None)   # Remove port5/SEG0 because it is already the base_segment
        for name, cevrf_seg in vrf_segs.items():
            cevrf_seg['ipmask'] =  cevrf_seg['ip_lxc'] + '/' + cevrf_seg['mask']
            cevrf_seg['gateway'] = str(ipaddress.ip_interface(cevrf_seg['ip']).ip)
            # Remove unused keys
            cevrf_seg.pop('ip'), cevrf_seg.pop('ip_lxc'), cevrf_seg.pop('subnet'), cevrf_seg.pop('mask')

        return {**base_segment, 'namespaces': vrf_segs, 'hosts': hosts }

    context = {
        # From HTML form
        'remote_internet': request.POST.get('remote_internet'),  # 'none', 'mpls', 'all'
        'bidir_sdwan': request.POST.get('bidir_sdwan'),  # 'none', 'route_tag', 'remote_sla', 'route_priority',
        'cross_region_advpn': bool(request.POST.get('cross_region_advpn', False)),  # True or False
        'full_mesh_ipsec': bool(request.POST.get('full_mesh_ipsec', False)),  # True or False
        'vrf_aware_overlay': bool(request.POST.get('vrf_aware_overlay', False)),  # True or False
        'advpnv2': bool(request.POST.get('advpnv2', False)),  # True or False
        'vrf_wan': int(request.POST.get('vrf_wan')),  # [0-251] VRF for Internet and MPLS links
        'vrf_pe': int(request.POST.get('vrf_pe')),  # [0-251] VRF for IPsec tunnels
        'vrf_seg0': int(request.POST.get('vrf_seg0')),  # [0-251] port5 (no vlan) segment
        # 'vrf_seg1': int(request.POST.get('vrf_seg1')),  # [0-251] vlan segment
        # 'vrf_seg2': int(request.POST.get('vrf_seg2')),  # [0-251] vlan segment
        'multicast': bool(request.POST.get('multicast', False)),  # True or False
        'br2br_routing': request.POST.get('br2br_routing'),  # 'strict_overlay_stickiness', 'hub_side_steering', 'fib'
        'shortcut_routing': request.POST.get('shortcut_routing'),  # 'no_advpn', 'exchange_ip', 'ipsec_selectors', 'dynamic_bgp'
        'bgp_design': request.POST.get('bgp_design'),  # 'per_overlay', 'per_overlay_legacy', 'on_loopback', 'no_bgp'
        'overlay': request.POST.get('overlay'),  # 'static' or 'mode_cfg'

        #
        'regional_advpn': None,  # 'boolean' defined later
        'bgp_route_reflection': None,  # 'boolean' defined later
        'bgp_aggregation': None,  # 'boolean' defined later
    }

    # Create the poc
    poc = FortiPoCAirbus(request)

    # Define the poc_id based on the options which were selected

    poc_id = None
    messages = []    # list of messages displayed along with the rendered configurations
    errors = []     # List of errors

    targetedFOSversion = FortiGate.FOS_int(request.POST.get('targetedFOSversion') or '0.0.0') # use '0.0.0' if empty targetedFOSversion string, FOS version becomes 0
    minimumFOSversion = 0

    if context['shortcut_routing'] == 'ipsec_selectors':
        minimumFOSversion = max(minimumFOSversion, 7_002_000)
    if context['vrf_aware_overlay']:
        minimumFOSversion = max(minimumFOSversion, 7_002_000)
    if context['bidir_sdwan'] == 'remote_sla':
        minimumFOSversion = max(minimumFOSversion, 7_002_001)
    if context['shortcut_routing'] == 'dynamic_bgp':
        minimumFOSversion = max(minimumFOSversion, 7_004_001)
    if context['advpnv2']:
        minimumFOSversion = max(minimumFOSversion, 7_004_002)

    if context['shortcut_routing'] == 'no_advpn':
        context['regional_advpn'] = context['cross_region_advpn'] = False
        context['bgp_route_reflection'] = False
        context['bgp_aggregation'] = True

    if context['shortcut_routing'] in ('ipsec_selectors', 'dynamic_bgp'):
        context['regional_advpn'] = True
        context['bgp_route_reflection'] = False
        context['bgp_aggregation'] = True

    if context['shortcut_routing'] == 'exchange_ip':
        context['regional_advpn'] = True
        context['bgp_route_reflection'] = True
        if context['cross_region_advpn']:
            context['bgp_aggregation'] = False
        else:
            context['bgp_aggregation'] = True

    if context['advpnv2']:
        if context['br2br_routing'] != 'fib':
            context['br2br_routing'] = 'fib'
            messages.append("ADVPN v2.0 no longer need any form of branch-to-branch routing strategy on the Hub. "
                            "So <b>Hub's br-2-br is forced to 'Simple FIB lookup'</b>")
    else:
        if context['shortcut_routing'] in ('ipsec_selectors', 'dynamic_bgp') and context['br2br_routing'] in ('strict_overlay_stickiness', 'fib'):
            messages.append(f"Hub's branch-to-branch routing strategy '{context['br2br_routing']}' prevents shortcut switchover on "
                    f"remote SLA failures when there is no BGP route-reflection because a shortcut does not hide its parent. "
                    f"<b>Forcing</b> Hub's branch-to-branch routing to <b>hub_side_steering</b>")
            context['br2br_routing'] = 'hub_side_steering'

    if context['shortcut_routing'] == 'dynamic_bgp' and not context['cross_region_advpn']:
        context['cross_region_advpn'] = True
        messages.append("cross_region_advpn is <b>forced</b> because dynamic BGP over shortcuts is used"
                        "<br>Need to test if cross-region shortcuts can be controlled with network-id and auto-discovery-crossover")

    if context['shortcut_routing'] == 'ipsec_selectors':
        if context['cross_region_advpn']:
            messages.append("Cross-regional branch-to-remoteHub shortcuts are <b>not possible</b>. See comments with CLI settings.")
        if context['vrf_aware_overlay']:
            context['vrf_aware_overlay'] = False  # shortcuts from ph2 selectors are incompatible with vpn-id-ipip
            messages.append("VRF-aware overlay was requested but is <b>forced to disable</b> since it is not supported with shortcuts from phase2 selectors")

    #
    # PoC 6 #####

    if context['bgp_design'] == 'per_overlay_legacy':  # BGP per overlay, legacy 6.4+ style
        poc_id = 6
        minimumFOSversion = max(minimumFOSversion, 6_004_000)

    #
    # PoC 9 #####

    if context['bgp_design'] == 'per_overlay':  # BGP per overlay, 7.0+ style
        poc_id = 9
        minimumFOSversion = max(minimumFOSversion, 7_000_000)

        if context['vrf_aware_overlay']:
            poc_id = None  # TODO
            errors.append("vrf_aware_overlay not yet available with BGP per overlay")

        if context['full_mesh_ipsec']:
            context['full_mesh_ipsec'] = False   # Full-mesh IPsec not implemented for bgp-per-overlay
            messages.append("Full-mesh IPsec not implemented for bgp-per-overlay: option is forced to 'False'")

        if context['br2br_routing'] == 'hub_side_steering':
            if context['bidir_sdwan'] == 'none':
                context['bidir_sdwan'] = 'route_priority'
                messages.append(f"Hub's branch-to-branch is set to '{context['br2br_routing']}' but Bidirectional SD-WAN is "
                                f"not set. <b>Forcing</b> bidirectional sd-wan to <b>'BGP priority'</b>")

            messages.append("'hub_side_steering' is only available for Hub's branch-to-branch routing within the same region. "
                            "It is not yet available for branch-to-remoteRegion where only strict_overlay_stickiness "
                            "is currently available over inter-regional tunnels")

        # if context['shortcut_routing'] == 'dynamic_bgp':
        #     errors.append("Dynamic BGP over shortcuts not yet available with BGP per overlay")

        if context['shortcut_routing'] == 'ipsec_selectors' and context['bidir_sdwan'] == 'remote_sla':
            context['bidir_sdwan'] = 'route_priority'
            messages.append("ADVPN from IPsec selectors <b>DOES NOT WORK with</b> bgp-per-overlay and <b>remote-sla</b>"
                            " (see comment in code). <b>Forcing 'BGP priority'</b>")

        if context['bidir_sdwan'] == 'remote_sla':
            context['overlay'] = 'static'   # remote-sla with bgp-per-overlay can only work with static-overlay IP@
            messages.append("Bidirectional SDWAN with 'remote-sla' was requested: <b>overlay is therefore forced to 'static'</b> since "
                           "remote-sla with bgp-per-overlay can only work with static-overlay IP@")

    #
    # PoC 10 #####

    if context['bgp_design'] == 'on_loopback':  # BGP on loopback, as of 7.0.4
        poc_id = 10
        minimumFOSversion = max(minimumFOSversion, 7_000_004)

        if context['bidir_sdwan'] in ('route_tag', 'route_priority'):  # 'or'
            context['bidir_sdwan'] = 'remote_sla'  # route_tag and route_priority only works with BGP per overlay
            messages.append("Bi-directional SD-WAN was requested: <b>method was forced to 'remote-sla'</b> which is the only "
                           "supported method with bgp-on-loopback")

        if context['br2br_routing'] == 'hub_side_steering' and context['bidir_sdwan'] == 'none':
            context['bidir_sdwan'] = 'remote_sla'
            messages.append(f"Hub's branch-to-branch is set to '{context['br2br_routing']}' but Bidirectional SD-WAN is "
                            f"not set. <b>Forcing</b> bidirectional sd-wan to <b>'remote-sla'</b>")

        if not context['multicast']:
            context['overlay'] = None   # Unnumbered IPsec tunnels are used if there is no need for multicast routing
            messages.append("Multicast is not requested: unnumbered IPsec tunnels are used")
        else:
            messages.append(f"Multicast is requested: <b>IPsec tunnels are numbered with '{context['overlay']}' overlay</b>")
            if context['vrf_aware_overlay']:
                messages.append(f"for multicast to work <b>PE VRF and BLUE VRF are forced to VRF 0</b>")
                context['vrf_pe'] = context['vrf_seg0'] = 0

        if context['vrf_aware_overlay']:
            # for vrf_name in ('vrf_wan', 'vrf_pe', 'vrf_seg0', 'vrf_seg1', 'vrf_seg2'):
            for vrf_name in ('vrf_wan', 'vrf_pe', 'vrf_seg0'):
                if context[vrf_name] > 251 or context[vrf_name] < 0:
                    poc_id = None; errors.append('VRF id must be within [0-251]')
            # if context['vrf_pe'] in (context['vrf_seg1'], context['vrf_seg2']):
            #     poc_id = None; errors.append("Only seg0/BLUE VRF can be in the same VRF as the PE VRF")
            # ce_vrfids = [context['vrf_seg0'], context['vrf_seg1'], context['vrf_seg2']] # list of all CE VRF IDs
            ce_vrfids = [context['vrf_seg0']] # list of all CE VRF IDs
            if len(set(ce_vrfids)) != len(ce_vrfids):  # check if the CE VRF IDs are all unique
                poc_id = None; errors.append('All CE VRF IDs must be unique')

            if context['cross_region_advpn'] and context['shortcut_routing'] == 'exchange_ip':
                messages.append("Cross-Regional ADVPN based off BGP NH convergence was requested but <b>this does not work</b> with VPNv4 eBGP next-hop-unchanged (tested with FOS 7.2.5)"
                                "<br>The BGP NH of VPNv4 prefixes is always set to the BGP loopback of the DC when advertised to eBGP peer"
                                "<br>It breaks all cross-regional shortcut routing convergence: inter-region branch-to-branch and inter-region branch-to-DC")

            if context['bgp_route_reflection']:
                messages.append("design choice: BGP Route-reflection (for ADVPN) is done only for VRFs BLUE and YELLOW. No RR (no ADPVPN) for VRF RED")

            messages.append("design choice: CE VRFs of WEST-BR1/BR2 have DIA while there is no DIA for the CE VRFs of EAST-BR1 (only RIA)")

    #
    # PoC x #####

    if context['bgp_design'] == 'no_bgp':  # No BGP, as of 7.2
        minimumFOSversion = max(minimumFOSversion, 7_002_000)
        poc_id = None   # TODO
        errors.append("SD-WAN+ADVPN design without BGP is not yet available")

    if poc_id is None:
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': errors})

    if targetedFOSversion and minimumFOSversion > targetedFOSversion:
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': f'The minimum version for the selected options is {minimumFOSversion:_}'})

    messages.insert(0, f"Minimum FortiOS version required for the selected set of features: {minimumFOSversion:_}")

    #
    # LAN underlays / segments
    #

    vrf = {
        'LAN': { 'vrfid': context['vrf_seg0'], 'vlanid': 0, 'alias': 'LAN_BLUE' },
        'SEGMENT_1': { 'vrfid': 1, 'vlanid': 1001, 'alias': 'LAN_YELLOW' },
        'SEGMENT_2': { 'vrfid': 2, 'vlanid': 1002, 'alias': 'LAN_RED' },
    }

    segments_devices = {
        'PARIS-DC': {
            'LAN': {'ip': '10.1.0.1/24', 'ip_lxc': '10.1.0.7', 'mac_lxc': '02:00:00:00:00:a1', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.1.10.1/24', 'ip_lxc': '10.1.10.7', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.1.20.1/24', 'ip_lxc': '10.1.20.7', **vrf['SEGMENT_2']},
        },
        'Toulouse': {
            'LAN': {'ip': '10.0.1.1/24', 'ip_lxc': '10.0.1.101', 'mac_lxc': '02:00:00:00:00:c1', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.0.11.1/24', 'ip_lxc': '10.0.11.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.0.21.1/24', 'ip_lxc': '10.0.21.101', **vrf['SEGMENT_2']},
        },
        'Dublin': {
            'LAN': {'ip': '10.0.2.1/24', 'ip_lxc': '10.0.2.101', 'mac_lxc': '02:00:00:00:00:d1', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.0.12.1/24', 'ip_lxc': '10.0.12.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.0.22.1/24', 'ip_lxc': '10.0.22.101', **vrf['SEGMENT_2']},
        },
        'Nantes': {
            'LAN': {'ip': '10.0.3.1/24', 'ip_lxc': '10.0.3.101', 'mac_lxc': '02:00:00:00:00:e1', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.0.13.1/24', 'ip_lxc': '10.0.13.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.0.23.1/24', 'ip_lxc': '10.0.23.101', **vrf['SEGMENT_2']},
        },
        'Greenlog': {
            'LAN': {'ip': '10.0.4.1/24', 'ip_lxc': '10.0.4.101', 'mac_lxc': '02:00:00:00:00:d2', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.0.14.1/24', 'ip_lxc': '10.0.14.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.0.24.1/24', 'ip_lxc': '10.0.24.101', **vrf['SEGMENT_2']},
        },
        'ASHBURN-DC': {
            'LAN': {'ip': '10.4.0.1/24', 'ip_lxc': '10.4.0.7', 'mac_lxc': '02:00:00:00:00:b1', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.4.10.1/24', 'ip_lxc': '10.4.10.7', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.4.20.1/24', 'ip_lxc': '10.4.20.7', **vrf['SEGMENT_2']},
        },
        'Ashburn': {
            'LAN': {'ip': '10.4.1.1/24', 'ip_lxc': '10.4.1.101', 'mac_lxc': '02:00:00:00:00:b2', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.4.11.1/24', 'ip_lxc': '10.4.11.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.4.21.1/24', 'ip_lxc': '10.4.21.101', **vrf['SEGMENT_2']},
        },
        'Yellow': {
            'LAN': {'ip': '10.4.2.1/24', 'ip_lxc': '10.4.2.101', 'mac_lxc': '02:00:00:00:00:f1', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.4.12.1/24', 'ip_lxc': '10.4.12.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.4.22.1/24', 'ip_lxc': '10.4.22.101', **vrf['SEGMENT_2']},
        },
        'RedAndYellow': {
            'LAN': {'ip': '10.4.3.1/24', 'ip_lxc': '10.4.3.101', 'mac_lxc': '02:00:00:00:00:f2', **vrf['LAN']},
            'SEGMENT_1': {'ip': '10.4.13.1/24', 'ip_lxc': '10.4.13.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.4.23.1/24', 'ip_lxc': '10.4.23.101', **vrf['SEGMENT_2']},
        },
    }

    # Restore the previous structure of the 'segments' to avoid having to change the jinja templates
    # add 'mask' and 'subnet'
    # change 'ip' from '10.10.10.1/24' to '10.10.10.1'
    compatiblize(segments_devices)

    # Allow segments in VRF x to access the Internet which is in VRF {{vrf_wan}}
    inter_segments = {}
    if context['vrf_aware_overlay']:
        inter_segments = {
            'BLUE_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.2', 'mask':'255.255.255.252'},
                            {'vrfid': context['vrf_seg0'], 'ip': '10.254.254.1', 'mask':'255.255.255.252'} ],
            'YELLOW_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.6', 'mask':'255.255.255.252'},
                            {'vrfid': vrf['SEGMENT_1']['vrfid'], 'ip': '10.254.254.5', 'mask':'255.255.255.252'} ],
            'RED_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.10', 'mask':'255.255.255.252'},
                            {'vrfid': vrf['SEGMENT_2']['vrfid'], 'ip': '10.254.254.9', 'mask':'255.255.255.252'} ]
        }
        if context['vrf_seg0'] == context['vrf_wan']:  # SEG0/port5 is in WAN VRF, it has direct access to WAN (INET)
            inter_segments.pop('BLUE_')  # remove it from the inter-segment list


    # DataCenters info used:
    # - by DCs:
    #   - as underlay interfaces IP@ for inter-regional tunnels (inet1/inet2/mpls)
    # - by the Branches:
    #   - as IPsec remote-gw IP@ (inet1/inet2/mpls)
    # - by both DCs and Branches:
    #   - as part of the computation of the networkid for Edge IPsec tunnels (id)

    dc_loopbacks = {
        'PARIS-DC': '10.200.1.254',
        'ASHBURN-DC': '10.200.2.254',
        'Toulouse': '10.200.1.1'
    }

    # Name and id of EAST devices is different between poc10 and other pocs (poc9, poc7)
    if poc_id == 10:  # PoC with BGP on loopback design: Regional LAN summaries are possible
        east_dc_ = {'name': 'EAST-DC1', 'generic_name': 'EAST-DC', 'dc_id': 1, 'lxc': 'PC-EAST-DC1'}
        east_br_ = {'name': 'EAST-BR1', 'generic_name': 'EAST-BR', 'branch_id': 1, 'lxc': 'PC-EAST-BR1'}
    else:  # Other PoCs with BGP per overlay design: No Regional LAN summaries (IP plan would overlap between Region)
        east_dc_ = {'name': 'EAST-DC3', 'generic_name': 'EAST-DC', 'dc_id': 3, 'lxc': 'PC-EAST-DC3'}
        east_br_ = {'name': 'EAST-BR3', 'generic_name': 'EAST-BR', 'branch_id': 3, 'lxc': 'PC-EAST-BR3'}

    paris_dc_ = {
                    'id': 1,
                    'inet1': FortiPoCAirbus.devices['PARIS-DC'].wan.inet1.subnet + '.1',  # 100.64.11.1
                    'inet2': FortiPoCAirbus.devices['PARIS-DC'].wan.inet2.subnet + '.1',  # 100.64.12.1
                    'mpls': FortiPoCAirbus.devices['PARIS-DC'].wan.mpls1.subnet + '.1',  # 10.0.14.1
                    'lan': lan_segment('PARIS-DC', poc, segments_devices)['ip'],
                    'loopback': dc_loopbacks['PARIS-DC']
                }

    ashburn_dc_ = {
                    'id': 3,
                    'inet1': FortiPoCAirbus.devices['ASHBURN-DC'].wan.inet1.subnet + '.3',  # 100.64.121.3
                    'inet2': FortiPoCAirbus.devices['ASHBURN-DC'].wan.inet2.subnet + '.3',  # 100.64.122.3
                    'mpls': FortiPoCAirbus.devices['ASHBURN-DC'].wan.mpls1.subnet + '.3',  # 10.0.124.3
                    'lan': lan_segment('ASHBURN-DC', poc, segments_devices)['ip'],
                    'loopback': dc_loopbacks['ASHBURN-DC']
                }

    toulouse_ = {
                    'id': 11,
                    'inet1': FortiPoCAirbus.devices['Toulouse'].wan.inet1.subnet + '.1',  # 100.64.11.1
                    'inet2': FortiPoCAirbus.devices['Toulouse'].wan.inet2.subnet + '.1',  # 100.64.12.1
                    'mpls': FortiPoCAirbus.devices['Toulouse'].wan.mpls1.subnet + '.1',  # 10.0.14.1
                    'lan': lan_segment('Toulouse', poc, segments_devices)['ip'],
                    'loopback': dc_loopbacks['Toulouse']
                }

    datacenters = {
            'west': {
                'first': paris_dc_,
                'second': paris_dc_,    # Fictitious
            },
            'east': {
                'first': ashburn_dc_,
                'second': ashburn_dc_   # Fictitious
            }
        }

    rendezvous_points = {}
    if context['multicast']:
        rendezvous_points = {
            'PARIS-DC': dc_loopbacks['PARIS-DC'],
        }

    # merge dictionaries
    context = {
        **context,
        'rendezvous_points': rendezvous_points
    }

    # 'direct_internet_access' is only for Branches. Hubs must have DIA, it's not optional.
    # 'inter_segments' describe the inter-vrf links used for DIA.

    paris_dc = FortiGate(name='PARIS-DC', template_group='DATACENTERS',
                         template_context={'region': 'West', 'region_id': 1, 'dc_id': 1,
                                           'loopback': dc_loopbacks['PARIS-DC'],
                                           'lan': lan_segment('PARIS-DC', poc, segments_devices),
                                           'vrf_segments': vrf_segments(segments_devices['PARIS-DC'],context),
                                           'inter_segments': inter_segments,
                                           'datacenter': datacenters,
                                           **context})
    toulouse = FortiGate(name='Toulouse', template_group='BRANCHES',
                         template_context={'region': 'West', 'region_id': 1, 'branch_id': 1,
                                           'loopback': dc_loopbacks['Toulouse'],
                                           'lan': lan_segment('Toulouse', poc, segments_devices),
                                           'vrf_segments': vrf_segments(segments_devices['Toulouse'],context),
                                           'direct_internet_access': True, 'inter_segments': inter_segments,
                                           'datacenter': datacenters['west'],
                                           **context})
    dublin = FortiGate(name='Dublin', template_group='BRANCHES',
                         template_context={'region': 'West', 'region_id': 1, 'branch_id': 2,
                                           'loopback': '10.200.1.2',
                                           'lan': lan_segment('Dublin', poc, segments_devices),
                                           'vrf_segments': vrf_segments(segments_devices['Dublin'],context),
                                           'direct_internet_access': False, # 'inter_segments': inter_segments,
                                           'datacenter': datacenters['west'],
                                           **context})
    nantes = FortiGate(name='Nantes', template_group='BRANCHES',
                         template_context={'region': 'West', 'region_id': 1, 'branch_id': 3,
                                           'loopback': '10.200.1.3',
                                           'lan': lan_segment('Nantes', poc, segments_devices),
                                           'vrf_segments': vrf_segments(segments_devices['Nantes'],context),
                                           'direct_internet_access': False, # 'inter_segments': inter_segments,
                                           'datacenter': {
                                               'first': toulouse_,
                                               'second': toulouse_
                                           },
                                           **context})
    greenlog = FortiGate(name='Greenlog', template_group='BRANCHES',
                         template_context={'region': 'West', 'region_id': 1, 'branch_id': 4,
                                           'loopback': '10.200.1.4',
                                           'lan': lan_segment('Greenlog', poc, segments_devices),
                                           'vrf_segments': vrf_segments(segments_devices['Greenlog'],context),
                                           'direct_internet_access': False, # 'inter_segments': inter_segments,
                                           'datacenter': {
                                               'first': toulouse_,
                                               'second': toulouse_
                                           },
                                           **context})

    ashburn_dc = FortiGate(name='ASHBURN-DC', template_group='DATACENTERS',
                        template_context={'region': 'East', 'region_id': 2, 'dc_id': 1,
                                          'loopback': dc_loopbacks['ASHBURN-DC'],
                                          'lan': lan_segment('ASHBURN-DC', poc, segments_devices),
                                          'vrf_segments': vrf_segments(segments_devices['ASHBURN-DC'], context),
                                          'inter_segments': inter_segments,
                                          'datacenter': datacenters,
                                          **context})
    ashburn_br = FortiGate(name='Ashburn', template_group='BRANCHES',
                        template_context={'region': 'East', 'region_id': 2, 'branch_id': 1,
                                          'loopback': '10.200.2.1',
                                          'lan': lan_segment('Ashburn', poc, segments_devices),
                                          'vrf_segments': vrf_segments(segments_devices['Ashburn'], context),
                                          'direct_internet_access': False,  # 'inter_segments': inter_segments,
                                          'datacenter': datacenters['east'],
                                          **context})
    yellow = FortiGate(name='Yellow', template_group='BRANCHES',
                        template_context={'region': 'East', 'region_id': 2, 'branch_id': 2,
                                          'loopback': '10.200.2.2',
                                          'lan': lan_segment('Yellow', poc, segments_devices),
                                          'vrf_segments': vrf_segments(segments_devices['Yellow'], context),
                                          'direct_internet_access': False,  # 'inter_segments': inter_segments,
                                          'datacenter': datacenters['east'],
                                          **context})
    redandyellow = FortiGate(name='RedAndYellow', template_group='BRANCHES',
                        template_context={'region': 'East', 'region_id': 2, 'branch_id': 3,
                                          'loopback': '10.200.2.3',
                                          'lan': lan_segment('RedAndYellow', poc, segments_devices),
                                          'vrf_segments': vrf_segments(segments_devices['RedAndYellow'], context),
                                          'direct_internet_access': False,  # 'inter_segments': inter_segments,
                                          'datacenter': datacenters['east'],
                                          **context})

    devices = {
        'PARIS-DC': paris_dc,
        'Ashburn': ashburn_br,
        'ASHBURN-DC': ashburn_dc,
        'Toulouse': toulouse,
        'Dublin': dublin,
        'Nantes': nantes,
        'Greenlog': greenlog,
        'Yellow': yellow,
        'RedAndYellow': redandyellow,

        'PC-PARIS-DC': LXC(name='PC-PARIS-DC', template_context=lxc_context('PARIS-DC', segments_devices, context)),
        'PC-Toulouse': LXC(name='PC-Toulouse', template_context=lxc_context('Toulouse', segments_devices, context)),
        'PC-Dublin': LXC(name='PC-Dublin', template_context=lxc_context('Dublin', segments_devices, context)),
        'PC-Nantes': LXC(name='PC-Nantes', template_context=lxc_context('Nantes', segments_devices, context)),
        'PC-Greenlog': LXC(name='PC-Greenlog', template_context=lxc_context('Greenlog', segments_devices, context)),
        'PC-Yellow': LXC(name='PC-Yellow', template_context=lxc_context('Yellow', segments_devices, context)),
        'PC-RedAndYellow': LXC(name='PC-RedAndYellow', template_context=lxc_context('RedAndYellow', segments_devices, context)),

        'PC-ASHBURN-DC': LXC(name='PC-ASHBURN-DC', template_context=lxc_context('ASHBURN-DC', segments_devices, context)),
        'PC-Ashburn': LXC(name='PC-Ashburn', template_context=lxc_context('Ashburn', segments_devices, context)),
    }

    # Update the poc
    poc.id = poc_id
    poc.minimum_FOS_version = minimumFOSversion
    poc.messages = messages

    # Check request, render and deploy configs
    return fpoc.start(poc, devices)
