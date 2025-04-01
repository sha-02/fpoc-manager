from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import copy

import fpoc
from fpoc.devices import Interface, FortiGate, LXC
from fpoc.FortiPoCSDWAN import FortiPoCSDWAN, FortiLabSDWAN, FabricStudioSDWAN
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
        'bgp_design': request.POST.get('bgp_design'),  # 'per_overlay', 'on_loopback'
        'overlay': request.POST.get('overlay'),  # 'no_ip' or 'static_ip' or 'mode_cfg'
        'full_mesh_ipsec': bool(request.POST.get('full_mesh_ipsec', False)),  # True or False
        'bidir_sdwan_bgp_priority': request.POST.get('bidir_sdwan_bgp_priority'),  # 'remote_sla_metrics', 'bgp_community', 'remote_sla_priority', 'remote_sla_status'
        'multicast': bool(request.POST.get('multicast', False)),  # True or False
        'vrf_aware_overlay': bool(request.POST.get('vrf_aware_overlay', False)),  # True or False
        'vrf_ria': request.POST.get('vrf_ria'),  # 'preserve_origin' or 'nat_origin'
        'vrf_wan': int(request.POST.get('vrf_wan')),  # [0-251] VRF for Internet and MPLS links
        'vrf_pe': int(request.POST.get('vrf_pe')),  # [0-251] VRF for IPsec tunnels
        'vrf_blue': int(request.POST.get('vrf_blue')),  # [0-251] port5 (no vlan) segment
        'vrf_yellow': int(request.POST.get('vrf_yellow')),  # [0-251] vlan segment
        'vrf_red': int(request.POST.get('vrf_red')),  # [0-251] vlan segment
    }

    # Create the poc
    if 'fortipoc' in request.path:  # poc is running in FortiPoC
        poc = FortiPoCSDWAN(request)
    elif 'fabric'  in request.path:  # poc is running in FabricStudio
        poc = FabricStudioSDWAN(request)
    else:  # poc is running in Hardware Lab
        poc = FortiLabSDWAN(request)

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
    # BGP on loopback - sanity checks

    if context['bgp_design'] == 'on_loopback':

        if context['bidir_sdwan_bgp_priority'] == 'bgp_community':
            context['bidir_sdwan_bgp_priority'] = 'remote_sla_metrics'  # bgp_community only works with BGP per overlay
            messages.append("Bi-directional SD-WAN from BGP community was requested but it is not supported by BGP on "
                            "loopback design. <b>Forcing to 'remote_sla_metrics'</b>")

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
                messages.append("<b>WAN VRF</b> (Internet +MPLS overlays) <b>is forced to VRF 1 </b> "
                                "(unlike PE VRF 0 to avoid configuring VRF leaking -- SNAT not possible in VRF 0)")
                context['vrf_wan'] = 1
                context['vrf_pe'] = context['vrf_blue'] = 0

                if context['vrf_ria'] == 'preserve_origin':
                    messages.append("preserve_origin is not yet implemented in context VRF segmentation + Multicast. "
                                    "<b>Forcing to nat_origin</b>")
                    context['vrf_ria'] = 'nat_origin'

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

        if context['bidir_sdwan_bgp_priority'] in ('remote_sla_metrics', 'remote_sla_priority', 'remote_sla_status'):
            messages.append(f"Bidirectional SDWAN with '{context['bidir_sdwan_bgp_priority']}' is requested but it can only work with static overlay IPs."
                            "<br>On the other hand, static overlays do not work with dynamic BGP on-loopback over shortcuts (details in '_restriction_no-static-IP-for-BGP-per-Overlay.md')."
                            f"<br>Consequently, it is not possible to combine '{context['bidir_sdwan_bgp_priority']}' and 'dynamic BGP': "
                            "BGP priority for Hub-side steering is <b>forced</b> to be based on <b>BGP community</b>")
            context['bidir_sdwan_bgp_priority'] = 'bgp_community'

        if context['vrf_aware_overlay']:
            context['vrf_aware_overlay'] = False
            messages.append("vrf_aware_overlay not yet tested with BGP per overlay: option is <b>forced to 'disable'</b>")

        if context['full_mesh_ipsec']:
            context['full_mesh_ipsec'] = False   # Full-mesh IPsec not implemented for bgp-per-overlay
            messages.append("Full-mesh IPsec not implemented for bgp-per-overlay: option is <b>forced to 'False'</b>")

    #
    # Final cleanup

    if not context['vrf_aware_overlay']:
        del(context['vrf_ria']); del(context['vrf_wan']); del(context['vrf_pe'])
        del(context['vrf_blue']); del(context['vrf_yellow']); del(context['vrf_red']);


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

    LAN = {
        'WEST-DC1': Interface(address='10.1.0.1/24'),
        'WEST-DC2': Interface(address='10.2.0.1/24'),
        'WEST-BR1': Interface(address='10.0.1.1/24'),
        'WEST-BR2': Interface(address='10.0.2.1/24'),
        'EAST-DC1': Interface(address='10.4.0.1/24'),
        'EAST-BR1': Interface(address='10.4.1.1/24'),
    }

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
                    'inet1': poc.devices['WEST-DC1'].wan.inet1,
                    'inet2': poc.devices['WEST-DC1'].wan.inet2,
                    'mpls': poc.devices['WEST-DC1'].wan.mpls1,
                    'lan': LAN['WEST-DC1'],
                    'loopback': dc_loopbacks['WEST-DC1']
                }

    west_dc2_ = {
                    'id': 2,
                    'inet1': poc.devices['WEST-DC2'].wan.inet1,
                    'inet2': poc.devices['WEST-DC2'].wan.inet2,
                    'mpls': poc.devices['WEST-DC2'].wan.mpls1,
                    'lan': LAN['WEST-DC2'],
                    'loopback': dc_loopbacks['WEST-DC2']
                }

    east_dc1_ = {
                    'id': 1,
                    'inet1': poc.devices['EAST-DC'].wan.inet1,
                    'inet2': poc.devices['EAST-DC'].wan.inet2,
                    'mpls': poc.devices['EAST-DC'].wan.mpls1,
                    'lan': LAN['EAST-DC1'],
                    'loopback': dc_loopbacks['EAST-DC1']
                }

    east_dc2_ = {  # Fictitious second DC for East region
                    'id': 2,
                    'inet1': poc.devices['EAST-DC'].wan.inet1,
                    'inet2': poc.devices['EAST-DC'].wan.inet2,
                    'mpls': poc.devices['EAST-DC'].wan.mpls1,
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

        context.update({'rendezvous_points': rendezvous_points})


    #
    # FortiGate Devices

    west_dc1 = FortiGate(name='WEST-DC1', template_group='DATACENTERS',
                         lan=LAN['WEST-DC1'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'dc_id': 1, 'gps': (48.856614, 2.352222),
                                           'loopback': dc_loopbacks['WEST-DC1'],
                                           'datacenter': datacenters,
                                           })
    west_dc2 = FortiGate(name='WEST-DC2', template_group='DATACENTERS',
                         lan=LAN['WEST-DC2'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'dc_id': 2, 'gps': (50.1109221, 8.6821267),
                                           'loopback': dc_loopbacks['WEST-DC2'],
                                           'datacenter': datacenters,
                                           })
    west_br1 = FortiGate(name='WEST-BR1', template_group='BRANCHES',
                         lan=LAN['WEST-BR1'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'branch_id': 1, 'gps': (44.8333, -0.5667),
                                           'loopback': '10.200.1.1',
                                           'datacenter': datacenters['west'],
                                           })
    west_br2 = FortiGate(name='WEST-BR2', template_group='BRANCHES',
                         lan=LAN['WEST-BR2'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'branch_id': 2, 'gps': (43.616354, 7.055222),
                                           'loopback': '10.200.1.2',
                                           'datacenter': datacenters['west'],
                                           })
    east_dc1 = FortiGate(name='EAST-DC1', template_group='DATACENTERS',
                        lan=LAN['EAST-DC1'],
                        template_context=context | {'region': 'East', 'region_id': 2, 'dc_id': 1, 'gps': (52.2296756, 21.0122287),
                                          'loopback': dc_loopbacks['EAST-DC1'],
                                           'datacenter': datacenters,
                                           })
    east_br1 = FortiGate(name='EAST-BR1', template_group='BRANCHES',
                        lan=LAN['EAST-BR1'],
                        template_context=context | {'region': 'East', 'region_id': 2, 'branch_id': 1, 'gps': (47.497912, 19.040235),
                                          'loopback': '10.200.2.1',
                                           'datacenter': datacenters['east'],
                                           })

    #
    # Host Devices used to build the /etc/hosts file

    hosts = {
        'PC-WEST-DC1': {'rank': 7, 'gateway': LAN['WEST-DC1'].ipprefix},
        'PC-WEST-DC2': {'rank': 7, 'gateway': LAN['WEST-DC2'].ipprefix},
        'PC-EAST-DC1': {'rank': 7, 'gateway': LAN['EAST-DC1'].ipprefix},
        'PC-WEST-BR1': {'rank': 101, 'gateway': LAN['WEST-BR1'].ipprefix},
        'PC-WEST-BR2': {'rank': 101, 'gateway': LAN['WEST-BR2'].ipprefix},
        'PC-EAST-BR1': {'rank': 101, 'gateway': LAN['EAST-BR1'].ipprefix},
    }

    devices = {
        'WEST-DC1': west_dc1,
        'WEST-DC2': west_dc2,
        'EAST-DC': east_dc1,    # 'DC' and not 'DC1' because it references the device in class FortiPoCSDWAN
        'WEST-BR1': west_br1,
        'WEST-BR2': west_br2,
        'EAST-BR': east_br1,    # 'BR' and not 'BR1' because it references the device in class FortiPoCSDWAN

        'WAN': FortiGate(name='WAN', template_filename='WAN.conf'),

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

        # Create a callback function to check if VDOMs must be enabled on FGT appliances with NPU ASIC
        # when VRF segmentation is done

        # As of 7.6.1, multi-vdom is no longer needed for VRF segmentation. So, the callback must now be registered at
        # the device level (which contains the FOS version) rather than at the poc level
        def multi_vdom(fgt: FortiGate):
            fgt.template_context['multi_vdom'] = not fgt.FOS >= 7_006_001   # multi-vdom no longer needed as of 7.6.1

        # Register the callback function for each NPU FGT in the 'devices' dict
        # Do not register the callback on poc.devices because at this stage these are the devices of the class itself
        # So the callback must be registered to the 'devices' in the dict
        # The dict 'devices' do not have the NPU info, so need to get this info from the class 'devices' (poc.devices)
        for devname, device in devices.items():
            if isinstance(device, FortiGate) and poc.devices[devname].npu:
                    device.callback_register(multi_vdom)

        # Before 7.6.1, the callback was done at poc level since all devices had to enable vdoms for VRF segmentation
        # def multi_vdom(poc: TypePoC):
        #     for fortigate in [device for device in poc.devices.values() if isinstance(device, FortiGate)]:
        #         fortigate.template_context['multi_vdom'] = bool(fortigate.npu)
        #
        # # Register the callback function
        # poc.callback_register(multi_vdom)

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
        'LAN': { 'vrfid': context['vrf_blue'], 'vlanid': 0, 'alias': 'LAN_BLUE' },
        'SEG_YELLOW': { 'vrfid': context['vrf_yellow'], 'alias': 'LAN_YELLOW' },
        'SEG_RED': { 'vrfid': context['vrf_red'], 'alias': 'LAN_RED' },
    }

    segments = {
        'WEST-DC1': {
            'LAN': Interface(address='10.1.0.1/24', **vrf['LAN']),
            'SEG_YELLOW': Interface(address='10.1.1.1/24', vlanid=16, **vrf['SEG_YELLOW']),
            'SEG_RED': Interface(address='10.1.2.1/24', vlanid=17, **vrf['SEG_RED']),
        },
        'WEST-DC2': {
            'LAN': Interface(address='10.2.0.1/24', **vrf['LAN']),
            'SEG_YELLOW': Interface(address='10.2.1.1/24', vlanid=26, **vrf['SEG_YELLOW']),
            'SEG_RED': Interface(address='10.2.2.1/24', vlanid=27, **vrf['SEG_RED']),
        },
        'WEST-BR1': {
            'LAN': Interface(address='10.0.1.1/24', **vrf['LAN']),
            'SEG_YELLOW': Interface(address='10.0.11.1/24', vlanid=36, **vrf['SEG_YELLOW']),
            'SEG_RED': Interface(address='10.0.12.1/24', vlanid=37, **vrf['SEG_RED']),
        },
        'WEST-BR2': {
            'LAN': Interface(address='10.0.2.1/24', **vrf['LAN']),
            'SEG_YELLOW': Interface(address='10.0.21.1/24', vlanid=46, **vrf['SEG_YELLOW']),
            'SEG_RED': Interface(address='10.0.22.1/24', vlanid=47, **vrf['SEG_RED']),
        },
        'EAST-DC': {
            'LAN': Interface(address='10.4.0.1/24', **vrf['LAN']),
            'SEG_YELLOW': Interface(address='10.4.1.1/24', vlanid=56, **vrf['SEG_YELLOW']),
            'SEG_RED': Interface(address='10.4.2.1/24', vlanid=57, **vrf['SEG_RED']),
        },
        'EAST-BR': {
            'LAN': Interface(address='10.4.1.1/24', **vrf['LAN']),
            'SEG_YELLOW': Interface(address='10.4.11.1/24', vlanid=66, **vrf['SEG_YELLOW']),
            'SEG_RED': Interface(address='10.4.12.1/24', vlanid=67, **vrf['SEG_RED']),
        },
    }

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
        # devices[name].template_context['lan'].update(vrf['LAN'])
        devices[name].lan.update(segments[name]['LAN'])
        devices[name].template_context['vrf_segments'] = segments[name]

        # Update Host Devices
        # devices[f'PC-{name}'].template_context['namespaces'] = segments[name]
        # devices[f'PC-{name}'].template_context['hosts'] = hosts
        devices[f'PC-{name}'].template_filename = 'lxc.vrf.conf'

    # 'inter_segments' describes the inter-vrf links

    for name in ('WEST-BR1', 'WEST-BR2', 'EAST-BR'):    # Branches
        devices[name].template_context['inter_segments'] = inter_segments

    for name in ('WEST-DC1', 'WEST-DC2', 'EAST-DC'):    # DCs
        devices[name].template_context['inter_segments'] = dc_inter_segments

