from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import copy

import fpoc
from fpoc import FortiGate, LXC
from fpoc.FortiPoCSDWAN import FortiPoCSDWAN
from fpoc.typing import TypePoC
import typing

import ipaddress


def dualdc(request: WSGIRequest) -> HttpResponse:
    """
    SDWAN+ADVPN v2.0
    Dual-Region WEST/EAST
    WEST: Dual DC, Two Branches
    EAST: Single DC, One Branch
    """

    context = {
        # From HTML form
        'bidir_sdwan_bgp_priority': request.POST.get('bidir_sdwan_bgp_priority'),  # 'remote_sla_priority', 'remote_sla_hc', 'bgp_community',
        'full_mesh_ipsec': bool(request.POST.get('full_mesh_ipsec', False)),  # True or False
        'vrf_aware_overlay': bool(request.POST.get('vrf_aware_overlay', False)),  # True or False
        'vrf_wan': int(request.POST.get('vrf_wan')),  # [0-251] VRF for Internet and MPLS links
        'vrf_pe': int(request.POST.get('vrf_pe')),  # [0-251] VRF for IPsec tunnels
        'vrf_blue': int(request.POST.get('vrf_blue')),  # [0-251] port5 (no vlan) segment
        'vrf_yellow': int(request.POST.get('vrf_yellow')),  # [0-251] vlan segment
        'vrf_red': int(request.POST.get('vrf_red')),  # [0-251] vlan segment
        'vrf_ria': request.POST.get('vrf_ria'),  # 'preserve_origin' or 'nat_origin'
        'multicast': bool(request.POST.get('multicast', False)),  # True or False
        'bgp_design': request.POST.get('bgp_design'),  # 'per_overlay', 'on_loopback'
        'overlay': request.POST.get('overlay'),  # 'no_ip' or 'static_ip' or 'mode_cfg'
    }

    # Create the poc
    poc = FortiPoCSDWAN(request)

    # Define the poc_id based on the options which were selected
    poc_id = 11
    messages = []    # list of messages displayed along with the rendered configurations
    errors = []     # List of errors

    targetedFOSversion = FortiGate.FOS_int(request.POST.get('targetedFOSversion') or '0.0.0') # use '0.0.0' if empty targetedFOSversion string, FOS version becomes 0
    minimumFOSversion = 7_004_004

    # ADVPNv2.0 bug with VRF segmentation fixed in 7.4.5 (1018427)
    if context['vrf_aware_overlay']:
        minimumFOSversion = 7_004_005

    #
    # Not yet done
    if context['bidir_sdwan_bgp_priority'] == 'remote_sla_priority':
        poc_id = None
        errors.append("Not yet implemented: Hub-side Steering BGP priority from priority in per-overlay Branch SD-WAN probes")


    #
    # BGP on loopback - sanity checks

    if context['bgp_design'] == 'on_loopback':

        if context['bidir_sdwan_bgp_priority'] == 'bgp_community':
            context['bidir_sdwan_bgp_priority'] = 'remote_sla_hc'  # bgp_community only works with BGP per overlay
            messages.append("Bi-directional SD-WAN was requested: <b>method was forced to 'remote-sla'</b> which is the only "
                           "supported method with bgp-on-loopback")

        if not context['multicast']:
            context['overlay'] = 'no_ip'   # Unnumbered IPsec tunnels are used if there is no need for multicast routing
            messages.append("Multicast is not requested: unnumbered IPsec tunnels are used")
        else:
            if context['overlay'] == 'no_ip':
                messages.append("Unnumbered overlay was requested but this is not possible for multicast so <b>forcing static IP</b> for overlays")
                context['overlay'] = 'static_ip'

            if context['overlay'] == 'mode_cfg':
                messages.append("Multicast is requested and IPsec tunnels are requested to be numbered with 'mode-cfg'. "
                    "As a side note: 'static' overlay IPs could be a better choice since it allows to "
                    "configure 'independent' shortcuts due to having independent BGP routing over shortcuts (dynamic BGP)")

            if context['vrf_aware_overlay']:
                messages.append("for multicast to work <b>PE VRF and BLUE VRF are forced to VRF 0</b>")
                context['vrf_pe'] = context['vrf_blue'] = 0

        if context['vrf_aware_overlay']:
            for vrf_name in ('vrf_wan', 'vrf_pe', 'vrf_blue', 'vrf_yellow', 'vrf_red'):
                if context[vrf_name] > 251 or context[vrf_name] < 0:
                    poc_id = None; errors.append('VRF id must be within [0-251]')
            if context['vrf_pe'] in (context['vrf_yellow'], context['vrf_red']):
                poc_id = None; errors.append("Only seg0/BLUE VRF can be in the same VRF as the PE VRF")
            ce_vrfids = [context['vrf_blue'], context['vrf_yellow'], context['vrf_red']] # list of all CE VRF IDs
            if len(set(ce_vrfids)) != len(ce_vrfids):  # check if the CE VRF IDs are all unique
                poc_id = None; errors.append('All CE VRF IDs must be unique')

            messages.append("design choice: All CE VRFs from all Branches in all Regions have DIA (there is no Branch with only RIA)")

    #
    # BGP per overlay - sanity checks

    if context['bgp_design'] == 'per_overlay':

        if context['overlay'] == 'no_ip':
            context['overlay'] = 'mode_cfg'
            messages.append("Unnumbered overlays were requested but this is not possible for BGP per overlay: "
                            "<b>dynamic (mode-cfg) overlay IPs</b> are configured")

        if context['overlay'] == 'static_ip':
            context['overlay'] = 'mode_cfg'
            messages.append("with setup (per-overlay BGP to Hub, on-loopback dynBGP for shortcuts) only dynamic overlay "
                            "works (details in '_restriction_no-static-IP-for-BGP-per-Overlay.md'). <b>Forcing to mode-cfg</b>")

        if context['bidir_sdwan_bgp_priority'] != 'bgp_community':
            context['bidir_sdwan_bgp_priority'] = 'bgp_community'
            messages.append("design choice: BGP priority for Hub-side steering is <b>forced</b> to be based on <b>BGP community</b>")

        if context['vrf_aware_overlay']:
            context['vrf_aware_overlay'] = False
            messages.append("vrf_aware_overlay not yet tested with BGP per overlay: option is <b>forced to 'disable'</b>")

        if context['full_mesh_ipsec']:
            context['full_mesh_ipsec'] = False   # Full-mesh IPsec not implemented for bgp-per-overlay
            messages.append("Full-mesh IPsec not implemented for bgp-per-overlay: option is <b>forced to 'False'</b>")

        if context['bidir_sdwan_bgp_priority'] == 'remote_sla_hc':
            context['overlay'] = 'static_ip'   # remote-sla with bgp-per-overlay can only work with static-overlay IP@
            messages.append("Bidirectional SDWAN with 'remote_sla_HC' is requested: <b>overlay is therefore forced to 'static'</b> since "
                           "remote-sla-HC with bgp-per-overlay can only work with static-overlay IP@")

    messages.insert(0, f"Minimum FortiOS version required for the selected set of features: {minimumFOSversion:_}")

    #
    # Display errors and Stop

    if poc_id is None:
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': errors})

    if targetedFOSversion and minimumFOSversion > targetedFOSversion:
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': f'The minimum version for the selected options is {minimumFOSversion:_}'})

    #
    # LAN underlays
    #

    fgt_ips = {
        'WEST-DC1': '10.1.0.1/24',
        'WEST-DC2': '10.2.0.1/24',
        'WEST-BR1': '10.0.1.1/24',
        'WEST-BR2': '10.0.2.1/24',
        'EAST-DC': '10.4.0.1/24', # DC and not DC1 because it is looked up against FortiPoCSDWAN
        'EAST-BR': '10.4.1.1/24', # DC and not DC1 because it is looked up against FortiPoCSDWAN
    }

    # From the FGT interface IP, construct a LAN dictionary containing port, ip, dotted mask, prefix length, subnet
    LAN = {}
    for devname, ipprefix in fgt_ips.items():
        LAN[devname] = {
            'port': poc.devices[devname].lan.port,  # eg, port5
            'ipprefix': ipprefix,   # eg, 10.1.0.1/24
            'ip' : str(ipaddress.ip_interface(ipprefix).ip),    # eg, 10.1.0.1
            'subnet' : str(ipaddress.ip_interface(ipprefix).network.network_address),   # eg, 10.1.0.0
            'mask': str(ipaddress.ip_interface(ipprefix).netmask),  # eg, 255.255.255.0
            'prefixlen': str(ipaddress.ip_interface(ipprefix).network.prefixlen),   # eg, 24
        }

    # "Replace" EAST-DC/EAST-BR by EAST-DC1/EAST-BR1
    LAN['EAST-DC1'] = LAN['EAST-DC']; del(LAN['EAST-DC'])
    LAN['EAST-BR1'] = LAN['EAST-BR']; del(LAN['EAST-BR'])

    # DataCenters info used:
    # - by DCs:
    #   - as underlay interfaces IP@ for inter-regional tunnels (inet1/inet2/mpls)
    # - by the Branches:
    #   - as IPsec remote-gw IP@ (inet1/inet2/mpls)
    # - by both DCs and Branches:
    #   - as part of the computation of the networkid for Edge IPsec tunnels (id)

    dc_loopbacks = {
        'WEST-DC1': '10.200.1.254',
        'WEST-DC2': '10.200.1.253',
        'EAST-DC1': '10.200.2.254',
        'EAST-DC2': '10.200.2.253',
    }

    # For bgp-per-overlay with BGP RR (legacy ADVPN shortcut routing) it was important that every Branch in every
    # region has a unique overlay IP address for each of its overlay tunnel (H{1|2}_INET{1|2}, H{1|2}_MPLS)
    # With shortcut routing based off dynamic BGP peering over shortcuts this is no longer needed
    # If bgp-per-overlay is done with the Hub then uniqueness of the overlay IP address is only within the region itself
    # So we don't need anymore that the 'id' of each Hub in the 'datacenters' dict be globally unique
    # it just needs to be unique within the region
    # So the 'id' of EAST-DC1/EAST-DC2 which were 3 and 4 respectively in previous design are now switched to 1 and 2

    west_dc1_ = {
                    'id': 1,
                    'inet1': FortiPoCSDWAN.devices['WEST-DC1'].wan.inet1.subnet + '.1',  # 100.64.11.1
                    'inet2': FortiPoCSDWAN.devices['WEST-DC1'].wan.inet2.subnet + '.1',  # 100.64.12.1
                    'mpls': FortiPoCSDWAN.devices['WEST-DC1'].wan.mpls1.subnet + '.1',  # 10.0.14.1
                    'lan': LAN['WEST-DC1'],
                    'loopback': dc_loopbacks['WEST-DC1']
                }

    west_dc2_ = {
                    'id': 2,
                    'inet1': FortiPoCSDWAN.devices['WEST-DC2'].wan.inet1.subnet + '.2',  # 100.64.21.2
                    'inet2': FortiPoCSDWAN.devices['WEST-DC2'].wan.inet2.subnet + '.2',  # 100.64.22.2
                    'mpls': FortiPoCSDWAN.devices['WEST-DC2'].wan.mpls1.subnet + '.2',  # 10.0.24.2
                    'lan': LAN['WEST-DC2'],
                    'loopback': dc_loopbacks['WEST-DC2']
                }

    east_dc1_ = {
                    'id': 1,
                    'inet1': FortiPoCSDWAN.devices['EAST-DC'].wan.inet1.subnet + '.3',  # 100.64.121.3
                    'inet2': FortiPoCSDWAN.devices['EAST-DC'].wan.inet2.subnet + '.3',  # 100.64.122.3
                    'mpls': FortiPoCSDWAN.devices['EAST-DC'].wan.mpls1.subnet + '.3',  # 10.0.124.3
                    'lan': LAN['EAST-DC1'],
                    'loopback': dc_loopbacks['EAST-DC1']
                }

    east_dc2_ = {  # Fictitious second DC for East region
                    'id': 2,
                    'inet1': FortiPoCSDWAN.devices['EAST-DC'].wan.inet1.subnet + '.4',  # 100.64.121.4
                    'inet2': FortiPoCSDWAN.devices['EAST-DC'].wan.inet2.subnet + '.4',  # 100.64.122.4
                    'mpls': FortiPoCSDWAN.devices['EAST-DC'].wan.mpls1.subnet + '.4',  # 10.0.124.4
                    'lan': '0.0.0.0/0',
                    'loopback': dc_loopbacks['EAST-DC2']
                }

    datacenters = {
            'west': {
                'first': west_dc1_,
                'second': west_dc2_,
            },
            'east': {
                'first': east_dc1_,
                'second': east_dc2_,  # Fictitious second DC for East region
            }
        }

    rendezvous_points = {}
    if context['multicast']:
        rendezvous_points = {
            'WEST-DC1': dc_loopbacks['WEST-DC1'],
            'WEST-DC2': dc_loopbacks['WEST-DC2'],
            'EAST-DC1': dc_loopbacks['EAST-DC1'],
        }

    # merge dictionaries
    context = {
        **context,
        'rendezvous_points': rendezvous_points
    }


    #
    # FortiGate Devices

    west_dc1 = FortiGate(name='WEST-DC1', template_group='DATACENTERS',
                         template_context={'region': 'West', 'region_id': 1, 'dc_id': 1, 'gps': (48.856614, 2.352222),
                                           'loopback': dc_loopbacks['WEST-DC1'],
                                           'lan':LAN['WEST-DC1'],
                                           'datacenter': datacenters,
                                           **context})
    west_dc2 = FortiGate(name='WEST-DC2', template_group='DATACENTERS',
                         template_context={'region': 'West', 'region_id': 1, 'dc_id': 2, 'gps': (50.1109221, 8.6821267),
                                           'loopback': dc_loopbacks['WEST-DC2'],
                                           'lan': LAN['WEST-DC2'],
                                           'datacenter': datacenters,
                                           **context})
    west_br1 = FortiGate(name='WEST-BR1', template_group='BRANCHES',
                         template_context={'region': 'West', 'region_id': 1, 'branch_id': 1, 'gps': (44.8333, -0.5667),
                                           'loopback': '10.200.1.1',
                                           'lan': LAN['WEST-BR1'],
                                           'datacenter': datacenters['west'],
                                           **context})
    west_br2 = FortiGate(name='WEST-BR2', template_group='BRANCHES',
                         template_context={'region': 'West', 'region_id': 1, 'branch_id': 2, 'gps': (43.616354, 7.055222),
                                           'loopback': '10.200.1.2',
                                           'lan': LAN['WEST-BR2'],
                                           'datacenter': datacenters['west'],
                                           **context})
    east_dc1 = FortiGate(name='EAST-DC1', template_group='DATACENTERS',
                        template_context={'region': 'East', 'region_id': 2, 'dc_id': 1, 'gps': (52.2296756, 21.0122287),
                                          'loopback': dc_loopbacks['EAST-DC1'],
                                          'lan': LAN['EAST-DC1'],
                                           'datacenter': datacenters,
                                           **context})
    east_br1 = FortiGate(name='EAST-BR1', template_group='BRANCHES',
                        template_context={'region': 'East', 'region_id': 2, 'branch_id': 1, 'gps': (47.497912, 19.040235),
                                          'loopback': '10.200.2.1',
                                          'lan': LAN['EAST-BR1'],
                                           'datacenter': datacenters['east'],
                                           **context})

    #
    # Host Devices used to build the /etc/hosts file

    hosts = {
        'PC-WEST-DC1': {'rank': 7, 'gateway': LAN['WEST-DC1']['ipprefix']},
        'PC-WEST-DC2': {'rank': 7, 'gateway': LAN['WEST-DC2']['ipprefix']},
        'PC-EAST-DC1': {'rank': 7, 'gateway': LAN['EAST-DC1']['ipprefix']},
        'PC-WEST-BR1': {'rank': 101, 'gateway': LAN['WEST-BR1']['ipprefix']},
        'PC-WEST-BR2': {'rank': 101, 'gateway': LAN['WEST-BR2']['ipprefix']},
        'PC-EAST-BR1': {'rank': 101, 'gateway': LAN['EAST-BR1']['ipprefix']},
    }

    devices = {
        'WEST-DC1': west_dc1,
        'WEST-DC2': west_dc2,
        'EAST-DC': east_dc1,    # 'DC' and not 'DC1' because it references the device in class FortiPoCSDWAN
        'WEST-BR1': west_br1,
        'WEST-BR2': west_br2,
        'EAST-BR': east_br1,    # 'BR' and not 'BR1' because it references the device in class FortiPoCSDWAN

        'PC-WEST-DC1': LXC(name="PC-WEST-DC1", template_context={'hosts': hosts}),
        'PC-WEST-DC2': LXC(name="PC-WEST-DC2",template_context={'hosts': hosts}),
        'PC-EAST-DC': LXC(name="PC-EAST-DC1", template_context={'hosts': hosts}),   # DC and not DC1
        'PC-WEST-BR1': LXC(name="PC-WEST-BR1",template_context={'hosts': hosts}),
        'PC-WEST-BR2': LXC(name="PC-WEST-BR2",template_context={'hosts': hosts}),
        'PC-EAST-BR': LXC(name="PC-EAST-BR1", template_context={'hosts': hosts}),   # BR and not BR1
        'INTERNET-SERVER': LXC(name="INTERNET-SERVER", template_filename='lxc.SRVINET.conf')
    }

    # Add VRF segmentation information to the poc
    #
    if context['vrf_aware_overlay']:
        vrf_segmentation(context, poc, devices)

    # Update the poc
    poc.id = poc_id
    poc.minimum_FOS_version = minimumFOSversion
    poc.messages = messages

    # Check request, render and deploy configs
    return fpoc.start(poc, devices)


###############################################################################################################
#
# VRF segmentation
#

# About VRF IDs (from Dmitry 'Managed SDWAN' workshop):
#
# The choice of PE VRF=1 is not completely arbitrary. While generally any non-zero PE VRF would work, we
# recommend using PE VRF=1 whenever possible, because it optimizes local-out traffic flows in some
# scenarios. While the detailed discussion is not in scope of this lab, we will simply mention that in certain
# situations the local-out traffic (such as the communication with FortiManager, FortiGuard and so on) may
# be taking an extra hop inside the FortiGate device, if the Internet VRF (which is the PE VRF!) has an ID
# higher than a CE VRF.
# Exactly for this reason the optimal configuration is when VRF=0 is not used, VRF=1 is configured as PE
# and the rest is left to CEs.
#

def vrf_segmentation(context: dict, poc: TypePoC, devices: typing.Mapping[str, typing.Union[FortiGate, LXC]]) -> None:
    vrf = {
        'LAN': { 'vrfid': context['vrf_blue'], 'vlanid': 0, 'color': 'BLUE', 'alias': 'LAN_BLUE' },
        'SEG_YELLOW': { 'vrfid': context['vrf_yellow'], 'vlanid': 100+context['vrf_yellow'], 'color': 'YELLOW', 'alias': 'LAN_YELLOW' },
        'SEG_RED': { 'vrfid': context['vrf_red'], 'vlanid': 100+context['vrf_red'], 'color': 'RED', 'alias': 'LAN_RED' },
    }

    segments = {
        'WEST-DC1': {
            'LAN': {'ip': '10.1.0.1/24', 'host_rank': 7, **vrf['LAN']},
            'SEG_YELLOW': {'ip': '10.1.1.1/24', 'host_rank': 7, **vrf['SEG_YELLOW']},
            'SEG_RED': {'ip': '10.1.2.1/24', 'host_rank': 7, **vrf['SEG_RED']},
        },
        'WEST-DC2': {
            'LAN': {'ip': '10.2.0.1/24', 'host_rank': 7, **vrf['LAN']},
            'SEG_YELLOW': {'ip': '10.2.1.1/24', 'host_rank': 7, **vrf['SEG_YELLOW']},
            'SEG_RED': {'ip': '10.2.2.1/24', 'host_rank': 7, **vrf['SEG_RED']},
        },
        'WEST-BR1': {
            'LAN': {'ip': '10.0.1.1/24', 'host_rank': 101, **vrf['LAN']},
            'SEG_YELLOW': {'ip': '10.0.11.1/24', 'host_rank': 101, **vrf['SEG_YELLOW']},
            'SEG_RED': {'ip': '10.0.12.1/24', 'host_rank': 101, **vrf['SEG_RED']},
        },
        'WEST-BR2': {
            'LAN': {'ip': '10.0.2.1/24', 'host_rank': 101, **vrf['LAN']},
            'SEG_YELLOW': {'ip': '10.0.21.1/24', 'host_rank': 101, **vrf['SEG_YELLOW']},
            'SEG_RED': {'ip': '10.0.22.1/24', 'host_rank': 101, **vrf['SEG_RED']},
        },
        'EAST-DC': {
            'LAN': {'ip': '10.4.0.1/24', 'host_rank': 7, **vrf['LAN']},
            'SEG_YELLOW': {'ip': '10.4.1.1/24', 'host_rank': 7, **vrf['SEG_YELLOW']},
            'SEG_RED': {'ip': '10.4.2.1/24', 'host_rank': 7, **vrf['SEG_RED']},
        },
        'EAST-BR': {
            'LAN': {'ip': '10.4.1.1/24', 'host_rank': 101, **vrf['LAN']},
            'SEG_YELLOW': {'ip': '10.4.11.1/24', 'host_rank': 101, **vrf['SEG_YELLOW']},
            'SEG_RED': {'ip': '10.4.12.1/24', 'host_rank': 101, **vrf['SEG_RED']},
        },
    }

    # Host Devices used to build the /etc/hosts file
    hosts = dict()
    for devname, segs in segments.items():
        for seg in segs.values():
            hostname = 'PC-'+devname+'-'+seg['color']   # eg, PC-WEST-DC1-BLUE
            hosts[hostname] = dict()
            hosts[hostname]['gateway'] = seg['ip']       # eg, 10.1.0.1/24  (IP@ of the IP gateway)
            hosts[hostname]['rank'] = seg['host_rank']   # eg, 7             (ie, IP@ is 10.1.0.7)

    # Restore the previous structure of the 'segments' to avoid having to change the jinja templates
    for segs in segments.values():
        for seg in segs.values():
            seg['ipprefix'] = seg['ip']     # 10.1.10.1/24
            seg['ip'] = str(ipaddress.ip_interface(seg['ip']).ip)   # 10.1.10.1
            seg['subnet'] = str(ipaddress.ip_interface(seg['ipprefix']).network.network_address) # 10.1.10.0
            seg['mask'] = str(ipaddress.ip_interface(seg['ipprefix']).netmask)  # 255.255.255.0
            seg['prefixlen'] = str(ipaddress.ip_interface(seg['ipprefix']).network.prefixlen)   # 24

    # Allow segments in VRF x to access the Internet which is in VRF {{vrf_wan}}
    inter_segments = {
        'BLUE_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.2', 'mask':'255.255.255.254'},
                        {'vrfid': context['vrf_blue'], 'ip': '10.254.254.3', 'mask':'255.255.255.254'} ],
        'YELLOW_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.4', 'mask':'255.255.255.254'},
                        {'vrfid': vrf['SEG_YELLOW']['vrfid'], 'ip': '10.254.254.5', 'mask':'255.255.255.254'} ],
        'RED_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.6', 'mask':'255.255.255.254'},
                        {'vrfid': vrf['SEG_RED']['vrfid'], 'ip': '10.254.254.7', 'mask':'255.255.255.254'} ],
    }

    if context['vrf_blue'] == context['vrf_wan']:  # SEG0/port5 is in WAN VRF, it has direct access to WAN (INET)
        inter_segments.pop('BLUE_')  # remove it from the inter-segment list

    # Hubs do not provide RIA service, they offer this service to other branches
    # so a single inter-vrf link per VRF is needed
    dc_inter_segments = copy.copy(inter_segments)

    if context['vrf_ria'] == 'preserve_origin':
        inter_segments.update(
            {
            'BLUE2_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.8', 'mask':'255.255.255.254'},
                            {'vrfid': context['vrf_blue'], 'ip': '10.254.254.9', 'mask':'255.255.255.254'} ],
            'YELLOW2_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.10', 'mask':'255.255.255.254'},
                            {'vrfid': vrf['SEG_YELLOW']['vrfid'], 'ip': '10.254.254.11', 'mask':'255.255.255.254'} ],
            'RED2_': [ {'vrfid': context['vrf_wan'], 'ip': '10.254.254.12', 'mask':'255.255.255.254'},
                            {'vrfid': vrf['SEG_RED']['vrfid'], 'ip': '10.254.254.13', 'mask':'255.255.255.254'} ]
            }
        )

        if context['vrf_blue'] == context['vrf_wan']:  # SEG0/port5 is in WAN VRF, it has direct access to WAN (INET)
            inter_segments.pop('BLUE2_')  # remove it from the inter-segment list


    #
    # Update FortiGate devices
    #

    for name in ('WEST-DC1', 'WEST-DC2', 'EAST-DC', 'WEST-BR1', 'WEST-BR2', 'EAST-BR'):
        devices[name].template_context['lan'].update(vrf['LAN'])
        devices[name].template_context['vrf_segments'] = segments[name]

        # Update Host Devices
        devices[f'PC-{name}'].template_context['namespaces'] = segments[name]
        devices[f'PC-{name}'].template_context['hosts'] = hosts
        devices[f'PC-{name}'].template_filename = 'lxc.vrf.conf'

    # 'inter_segments' describes the inter-vrf links

    for name in ('WEST-BR1', 'WEST-BR2', 'EAST-BR'):    # Branches
        devices[name].template_context['inter_segments'] = inter_segments

    for name in ('WEST-DC1', 'WEST-DC2', 'EAST-DC'):    # DCs
        devices[name].template_context['inter_segments'] = dc_inter_segments

