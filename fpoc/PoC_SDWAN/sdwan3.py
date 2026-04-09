from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import copy

import fpoc
from fpoc import AbortDeployment
from fpoc.devices import Interface, FortiGate, LXC
from fpoc.PoC_SDWAN import AgoraSDWAN, FabricStudioSDWAN
from fpoc.typing import TypePoC
import typing

import ipaddress


def dualdc(request: WSGIRequest) -> HttpResponse:
    """
    PoC12, FortiOS >= 8.0
        BGP on loopback, SDWAN+ADVPN v2.0, ADVPN routing with dynamic BGP on loopback
        Hub-side Steering with BGP priority from embedded priority in per-overlay SD-WAN probes
        VRF segmentation with new 8.0 VRF design

    Dual-Region WEST/EAST
        no SNAT to WEST-EXT: Remote Signaling with BGP MED automatically derived from link priority

    WEST: Dual DC, Two Branches
    EAST: Single DC, One Branch
    """
    context = {
        # From HTML form
        'overlay': request.POST.get('overlay'),  # 'no_ip' or 'static_ip' or 'mode_cfg'
        'full_mesh_ipsec': bool(request.POST.get('full_mesh_ipsec', False)),  # True or False
        'dualHub_failover': request.POST.get('dualHub_failover'),  # 'lowest-cost', 'best-link'
        'multicast': bool(request.POST.get('multicast', False)),  # True or False
        'corporate_summary': request.POST.get('corporate_summary'),  # 'rfc1918', 'net10'

        # VRF segmentation
        'vrf_aware_overlay': bool(request.POST.get('vrf_aware_overlay', False)),  # True or False
        'vrf_wan': int(request.POST.get('vrf_wan')),  # [0-511] VRF for Internet and MPLS links
        'vrf_pe': int(request.POST.get('vrf_pe')),  # [0-511] VRF for IPsec tunnels
        'vrf_blue': int(request.POST.get('vrf_blue')),  # [0-511] port5 (no vlan) segment
        'vrf_yellow': int(request.POST.get('vrf_yellow')),  # [0-511] vlan segment
        'vrf_red': int(request.POST.get('vrf_red')),  # [0-511] vlan segment
        'vrf_grey': int(request.POST.get('vrf_grey', 10)),  # VRF between WEST-DCs and WEST-EXT

        # FMG
        'fortimanager': bool(request.POST.get('fortimanager', False)),  # True or False
        'fmg_sn': request.POST.get('fmg_sn'),

        # These context are no longer use, they were used for design choices in previous FOS versions
        # They are still in the HTML form, but as hidden, with a fixed value. They are just kept "just in case".
        'bgp_design': request.POST.get('bgp_design'),  # 'on_loopback'
        'bidir_sdwan_bgp_priority': request.POST.get('bidir_sdwan_bgp_priority'),  # 'remote_sla_priority'
        'remote_signaling': request.POST.get('remote_signaling'),  # 'branch_MED'
    }

    # Define the poc_id based on the options which were selected
    poc_id = 12
    messages = []    # list of messages displayed along with the rendered configurations
    errors = []     # List of errors

    targetedFOSversion = FortiGate.FOS_int(request.POST.get('targetedFOSversion') or '0.0.0') # use '0.0.0' if empty targetedFOSversion string, FOS version becomes 0

    # Minimum FOS version
    minimumFOSversion = 8_000_000

    #
    # central-management - sanity checks
    if context['fortimanager'] and not context['fmg_sn'].startswith('FMG-'):
        errors.append('central-management is requested by the FMG S/N is incorrect')

    #
    # Sanity checks

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


    if context['vrf_aware_overlay']: # VRF segmentation
        ce_vrfs = [context['vrf_blue'], context['vrf_yellow'], context['vrf_red'], context['vrf_grey']]  # List of VRF IDs of all CEs
        for vrfid in [context['vrf_wan'], context['vrf_pe']] + ce_vrfs:
            if vrfid > 511 or vrfid < 0:
                errors.append('VRF id must be within [0-511]')

        if context['vrf_wan'] != context['vrf_pe']:
            errors.append('vrf_wan and vrf_pe must be identical in current jinja code (TBD)')

        vrfids = [context['vrf_pe']] + ce_vrfs # list of all PE+CE VRF IDs
        if len(set(vrfids)) != len(vrfids):  # check if the VRF IDs are all unique
            errors.append('VRF IDs for PE and CE must all be unique. Current List of IDs='+repr(vrfids))

        messages.append("design choice: All CE VRFs from all Branches in all Regions have DIA + SSE RIA (no RIA via HUB)")
        messages.append("design choice: WEST-EXT resources (10.12.0.0/24) are leaked from VRF GREY to all CE VRFs (BLUE, RED, YELLOW)")

    else: # no VRF segmentation: underlay and overlay traffic goes to VRF WAN
        if context['vrf_wan'] > 511 or context['vrf_wan'] < 0:
            messages.append('Incorrect VRF id for VRF WAN, <b>forcing to 1</b>')
            context['vrf_wan'] = 1

        context['vrf_pe'] = context['vrf_wan']
        messages.append(f"Underlay and Overlay are configured in VRF WAN: {context['vrf_wan']}")


    #
    # Final cleanup

    if not context['vrf_aware_overlay']:    # only keep vrf_wan and vrf_pe which are always used, regardless of vrf-segmentation
        del(context['vrf_blue']); del(context['vrf_yellow']); del(context['vrf_red']); del(context['vrf_grey'])


    messages.insert(0, f"Minimum FortiOS version required for the selected set of features: {minimumFOSversion:_}")

    #
    # Display errors and Stop

    if errors:
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': errors})

    if targetedFOSversion and minimumFOSversion > targetedFOSversion:
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': f'The minimum version for the selected options is {minimumFOSversion:_}'})

    #
    # Create the poc
    #
    if 'fabric'  in request.path:  # poc is running in FabricStudio
        poc = FabricStudioSDWAN(request)
    elif 'hardware' in request.path:  # poc is running in Hardware Lab
        poc = AgoraSDWAN(request)
    else:
        print('\nError: Cannot create the poc based on the request PATH')
        raise AbortDeployment

    # FOS 8.0+ new VRF design, VRF 0 is no longer a union of all VRFs for local-out
    # So, in this PoC, OOB is in VRF 0 (instead of 10 in previous PoCs)
    poc.mgmt.vrfid = 0

    #
    # LAN underlays
    #

    LAN = {
        'WEST-DC1': Interface(address='10.1.0.1/24', alias='DC'),
        'WEST-DC2': Interface(address='10.2.0.1/24', alias='DC'),
        'WEST-BR1': Interface(address='10.0.1.1/24', alias='LAN'),
        'WEST-BR2': Interface(address='10.0.2.1/24', alias='LAN'),
        'EAST-DC1': Interface(address='10.4.0.1/24', alias='DC'),
        'EAST-BR1': Interface(address='10.4.1.1/24', alias='LAN'),
        'EAST-BR2': Interface(address='10.4.2.1/24', alias='LAN'),
    }

    # DataCenters info used:
    # - by DCs:
    #   - as underlay interfaces IP@ for inter-regional tunnels (inet1/inet2/mpls)
    # - by the Branches:
    #   - as IPsec remote-gw IP@ (inet1/inet2/mpls)
    # - by both DCs and Branches:
    #   - as part of the computation of the networkid for Edge IPsec tunnels (id)

    dc_loopbacks = {
        'WEST-DC1': '10.200.1.251',
        'WEST-DC2': '10.200.1.252',
        'EAST-DC1': '10.200.2.251',
        'EAST-DC2': '10.200.2.252',
    }

    # We don't need that the 'id' of each Hub in the 'datacenters' dict be globally unique, it just needs to be unique
    # within its region

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
                    'inet1': poc.devices['EAST-DC1'].wan.inet1,
                    'inet2': poc.devices['EAST-DC1'].wan.inet2,
                    'mpls': poc.devices['EAST-DC1'].wan.mpls1,
                    'lan': LAN['EAST-DC1'],
                    'loopback': dc_loopbacks['EAST-DC1']
                }

    east_dc2_ = {  # Fictitious second DC for East region
                    'id': 2,
                    'inet1': poc.devices['EAST-DC1'].wan.inet1,
                    'inet2': poc.devices['EAST-DC1'].wan.inet2,
                    'mpls': poc.devices['EAST-DC1'].wan.mpls1,
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
                                'datacenter': datacenters
                                })
    west_dc2 = FortiGate(name='WEST-DC2', template_group='DATACENTERS',
                         lan=LAN['WEST-DC2'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'dc_id': 2, 'gps': (50.1109221, 8.6821267),
                                'loopback': dc_loopbacks['WEST-DC2'],
                                'datacenter': datacenters
                                })
    west_br1 = FortiGate(name='WEST-BR1', template_group='BRANCHES',
                         lan=LAN['WEST-BR1'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'branch_id': 1, 'gps': (44.8333, -0.5667),
                                'loopback': '10.200.1.1',
                                'datacenter': datacenters['west']
                             })
    west_br2 = FortiGate(name='WEST-BR2', template_group='BRANCHES',
                         lan=LAN['WEST-BR2'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'branch_id': 2, 'gps': (43.616354, 7.055222),
                                'loopback': '10.200.1.2',
                                'datacenter': datacenters['west']
                                 })
    east_dc1 = FortiGate(name='EAST-DC1', template_group='DATACENTERS',
                        lan=LAN['EAST-DC1'],
                        template_context=context | {'region': 'East', 'region_id': 2, 'dc_id': 1, 'gps': (52.2296756, 21.0122287),
                                'loopback': dc_loopbacks['EAST-DC1'],
                                'datacenter': datacenters
                                })
    east_br1 = FortiGate(name='EAST-BR1', template_group='BRANCHES',
                        lan=LAN['EAST-BR1'],
                        template_context=context | {'region': 'East', 'region_id': 2, 'branch_id': 1, 'gps': (47.497912, 19.040235),
                                'loopback': '10.200.2.1',
                                'datacenter': datacenters['east']
                                })
    east_br2 = FortiGate(name='EAST-BR2', template_group='BRANCHES',
                        lan=LAN['EAST-BR2'],
                        template_context=context | {'region': 'East', 'region_id': 2, 'branch_id': 2, 'gps': (44.4323, 26.1063),
                                'loopback': '10.200.2.2',
                                'datacenter': datacenters['east']
                                })

    #
    # Host Devices used to build the /etc/hosts file

    hosts = {
        'WEST-DC1-LXC': {'rank': 7, 'gateway': LAN['WEST-DC1'].ipprefix},
        'WEST-DC2-LXC': {'rank': 7, 'gateway': LAN['WEST-DC2'].ipprefix},
        'EAST-DC1-LXC': {'rank': 7, 'gateway': LAN['EAST-DC1'].ipprefix},
        'WEST-BR1-LXC': {'rank': 101, 'gateway': LAN['WEST-BR1'].ipprefix},
        'WEST-BR2-LXC': {'rank': 101, 'gateway': LAN['WEST-BR2'].ipprefix},
        'EAST-BR1-LXC': {'rank': 101, 'gateway': LAN['EAST-BR1'].ipprefix},
        'EAST-BR2-LXC': {'rank': 101, 'gateway': LAN['EAST-BR2'].ipprefix},
    }

    devices = {
        'WEST-DC1': west_dc1,
        'WEST-DC2': west_dc2,
        'EAST-DC1': east_dc1,
        'WEST-BR1': west_br1,
        'WEST-BR2': west_br2,
        'EAST-BR1': east_br1,
        # 'EAST-BR2': east_br2,

        # 'WAN': FortiGate(name='WAN', template_filename='WAN.conf'),

        'WEST-DC1-LXC': LXC(name="WEST-DC1-LXC", template_context={'hosts': hosts}),
        'WEST-DC2-LXC': LXC(name="WEST-DC2-LXC",template_context={'hosts': hosts}),
        'EAST-DC1-LXC': LXC(name="EAST-DC1-LXC", template_context={'hosts': hosts}),
        'WEST-BR1-LXC': LXC(name="WEST-BR1-LXC",template_context={'hosts': hosts}),
        'WEST-BR2-LXC': LXC(name="WEST-BR2-LXC",template_context={'hosts': hosts}),
        'EAST-BR1-LXC': LXC(name="EAST-BR1-LXC", template_context={'hosts': hosts}),
        'EAST-BR2-LXC': LXC(name="EAST-BR2-LXC", template_context={'hosts': hosts}),
        'INTERNET-SERVER': LXC(name="INTERNET-SERVER", template_filename='lxc.SRVINET.conf')
    }

    # Add VRF segmentation information to the poc
    #
    if context['vrf_aware_overlay']:
        vrf_segmentation(context, poc, devices)

    # Update the poc (monkey patching)
    poc.id = poc_id
    poc.minimum_FOS_version = minimumFOSversion
    poc.messages = messages

    # Check request, render and deploy configs
    return fpoc.start(poc, devices)


###############################################################################################################
#
# VRF segmentation
#

def vrf_segmentation(context: dict, poc: TypePoC, devices: typing.Mapping[str, typing.Union[FortiGate, LXC]]) -> None:
    segments = {
        'WEST-DC1': {
            'LAN': Interface(address='10.1.0.1/24', port='port5', vlanid=0, alias='LAN_BLUE', vrfid=context['vrf_blue']),
            'LAN_YELLOW': Interface(address='10.1.1.1/24', port='port5', vlanid=16, name='LAN_YELLOW', vrfid=context['vrf_yellow']),
            'LAN_RED': Interface(address='10.1.2.1/24', port='port5', vlanid=17, name='LAN_RED', vrfid=context['vrf_red']),
            'LAN_GREY': Interface(address='10.1.255.1/24', port='port5', vlanid=18, name='LAN_GREY', vrfid=context['vrf_grey']),
        },
        'WEST-DC2': {
            'LAN': Interface(address='10.2.0.1/24', port='port5', vlanid=0, alias='LAN_BLUE', vrfid=context['vrf_blue']),
            'LAN_YELLOW': Interface(address='10.2.1.1/24', port='port5', vlanid=26, name='LAN_YELLOW', vrfid=context['vrf_yellow']),
            'LAN_RED': Interface(address='10.2.2.1/24', port='port5', vlanid=27, name='LAN_RED', vrfid=context['vrf_red']),
            'LAN_GREY': Interface(address='10.2.255.1/24', port='port5', vlanid=28, name='LAN_GREY', vrfid=context['vrf_grey']),
        },
        'WEST-BR1': {
            'LAN': Interface(address='10.0.1.1/24', port='port5', vlanid=0, alias='LAN_BLUE', vrfid=context['vrf_blue']),
            'LAN_YELLOW': Interface(address='10.0.11.1/24', port='port5', vlanid=36, name='LAN_YELLOW', vrfid=context['vrf_yellow']),
            'LAN_RED': Interface(address='10.0.12.1/24', port='port5', vlanid=37, name='LAN_RED', vrfid=context['vrf_red']),
        },
        'WEST-BR2': {
            'LAN': Interface(address='10.0.2.1/24', port='port5', vlanid=0, alias='LAN_BLUE', vrfid=context['vrf_blue']),
            'LAN_YELLOW': Interface(address='10.0.21.1/24', port='port5', vlanid=46, name='LAN_YELLOW', vrfid=context['vrf_yellow']),
            'LAN_RED': Interface(address='10.0.22.1/24', port='port5', vlanid=47, name='LAN_RED', vrfid=context['vrf_red']),
        },
        'EAST-DC1': {
            'LAN': Interface(address='10.4.0.1/24', port='port5', vlanid=0, alias='LAN_BLUE', vrfid=context['vrf_blue']),
            'LAN_YELLOW': Interface(address='10.4.1.1/24', port='port5', vlanid=56, name='LAN_YELLOW', vrfid=context['vrf_yellow']),
            'LAN_RED': Interface(address='10.4.2.1/24', port='port5', vlanid=57, name='LAN_RED', vrfid=context['vrf_red']),
        },
        'EAST-BR1': {
            'LAN': Interface(address='10.4.1.1/24', port='port5', vlanid=0, alias='LAN_BLUE', vrfid=context['vrf_blue']),
            'LAN_YELLOW': Interface(address='10.4.11.1/24', port='port5', vlanid=66, name='LAN_YELLOW', vrfid=context['vrf_yellow']),
            'LAN_RED': Interface(address='10.4.12.1/24', port='port5', vlanid=67, name='LAN_RED', vrfid=context['vrf_red']),
        },
        'EAST-BR2': {
            'LAN': Interface(address='10.4.2.1/24', port='port5', vlanid=0, alias='LAN_BLUE', vrfid=context['vrf_blue']),
            'LAN_YELLOW': Interface(address='10.4.21.1/24', port='port5', vlanid=76, name='LAN_YELLOW', vrfid=context['vrf_yellow']),
            'LAN_RED': Interface(address='10.4.22.1/24', port='port5', vlanid=77, name='LAN_RED', vrfid=context['vrf_red']),
        },
    }

    #
    # Update FortiGate devices
    #
    for device in devices.values():
        if isinstance(device,FortiGate):
            device.lan.update(segments[device.name]['LAN'])
            device.template_context['vrf_segments'] = segments[device.name]
