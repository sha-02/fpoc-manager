from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
import copy

import fpoc
from fpoc.devices import Interface, FortiGate, WAN
from .once import FabricStudioPoCOnce


def poc02(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    FOS 7.6.7
    Dual Region, Single Hub per Region, 4x Branches (2x BR per Region)
    3x VRFs: IPv4/VPNv4 & IPv6/VPNv6
    multicast IPv4 in VRFs
    EVPN
    No local breakout, only overlay traffic
    """

    #
    # Create the poc
    #
    poc = FabricStudioPoCOnce(request)

    poc.id = poc_id
    poc.minimum_FOS_version = 7_006_007
    poc.messages = []
    poc.mgmt.vrfid = 1

    #
    # Define devices and rendering context
    #

    context = {
        'overlay': 'no_ip',
        'full_mesh_ipsec': False,
        'dualHub_failover': 'lowest-cost', # 'lowest-cost', 'best-link'
        'corporate_summary': 'rfc1918', # 'rfc1918', 'net10'
        'dia': False, 'sia': False, 'ria': False, 'ria_only': False,

        'multicast': True,

        # VRF segmentation
        # vrf_evpn must be 0 and, from my test results, it forces using vrf_pe as 0 as well
        'vrf_segmentation': True,
        'vrf_wan': 2,
        'vrf_pe': 0,
        'vrf_evpn': 0,
        'vrf_data': 10,
        'vrf_voice': 11,
        'vrf_video': 12,

        # EVPN
        'evpn': True,
        'evpn_anycast_gw': False,    # Use same GW IP on all leafs of the same segment

        # FMG
        'fortimanager': False, 'fmg_sn': None,
    }

    # For aliases in boostrap config
    context |= {
        'ipv6': True, 'vpnv4': True, 'vpnv6': True,
        'vrfs': [ ('pe', context['vrf_pe']), ('data', context['vrf_data']), ('voice', context['vrf_voice']),
                  ('video', context['vrf_video']) ],
        'mcgroups': [ ('voice', '239.11.11.11'), ('video', '239.12.12.12') ]
    }

    #
    # LAN underlays
    #

    segments = {
        'HUB1': {
            'DATA': Interface(address='192.168.1.11/31', port='port5', vlanid=15, name='DATA', vrfid=context['vrf_data']),
            'VOICE': Interface(address='192.168.1.12/31', port='port5', vlanid=16, name='VOICE', vrfid=context['vrf_voice']),
            'VIDEO': Interface(address='192.168.1.14/31', port='port5', vlanid=17, name='VIDEO', vrfid=context['vrf_video']),
        },
        'HUB2': {
            'DATA': Interface(address='192.168.2.11/31', port='port5', vlanid=25, name='DATA', vrfid=context['vrf_data']),
            'VOICE': Interface(address='192.168.2.12/31', port='port5', vlanid=26, name='VOICE', vrfid=context['vrf_voice']),
            'VIDEO': Interface(address='192.168.2.14/31', port='port5', vlanid=27, name='VIDEO', vrfid=context['vrf_video']),
        },
        'BRANCH1': {
            'LAN': Interface(address='10.1.10.1/24', port='port5', vlanid=0, alias='LAN_DATA', vrfid=context['vrf_data']),
            'LAN_VOICE': Interface(address='10.1.11.1/24', port='port5', vlanid=36, name='LAN_VOICE', vrfid=context['vrf_voice']),
            'LAN_VIDEO': Interface(address='10.1.12.1/24', port='port5', vlanid=37, name='LAN_VIDEO', vrfid=context['vrf_video']),
        },
        'BRANCH2': {
            'LAN': Interface(address='10.2.10.1/24', port='port5', vlanid=0, alias='LAN_DATA', vrfid=context['vrf_data']),
            'LAN_VOICE': Interface(address='10.2.11.1/24', port='port5', vlanid=46, name='LAN_VOICE', vrfid=context['vrf_voice']),
            'LAN_VIDEO': Interface(address='10.2.12.1/24', port='port5', vlanid=47, name='LAN_VIDEO', vrfid=context['vrf_video']),
        },
        'BRANCH3': {
            'LAN': Interface(address='10.3.10.1/24', port='port5', vlanid=0, alias='LAN_DATA', vrfid=context['vrf_data']),
            'LAN_VOICE': Interface(address='10.3.11.1/24', port='port5', vlanid=66, name='LAN_VOICE', vrfid=context['vrf_voice']),
            'LAN_VIDEO': Interface(address='10.3.12.1/24', port='port5', vlanid=67, name='LAN_VIDEO', vrfid=context['vrf_video']),
        },
        'BRANCH4': {
            'LAN': Interface(address='10.4.10.1/24', port='port5', vlanid=0, alias='LAN_DATA', vrfid=context['vrf_data']),
            'LAN_VOICE': Interface(address='10.4.11.1/24', port='port5', vlanid=76, name='LAN_VOICE', vrfid=context['vrf_voice']),
            'LAN_VIDEO': Interface(address='10.4.12.1/24', port='port5', vlanid=77, name='LAN_VIDEO', vrfid=context['vrf_video']),
        },
    }

    dc_loopbacks = {
        'HUB1': '10.200.1.251',
        'HUB2': '10.200.2.251',
    }

    hub1_ = {
                    'id': 1,
                    'inet1': poc.devices['HUB1'].wan.inet1,
                    'inet2': poc.devices['HUB1'].wan.inet2,
                    'inet3': poc.devices['HUB1'].wan.inet3,
                    'mpls': poc.devices['HUB1'].wan.mpls1,
                    # 'lan': PE['HUB1'],
                    'lan': segments['HUB1']['DATA'],
                    'loopback': dc_loopbacks['HUB1'],
                }

    hub2_ = {
                    'id': 2,
                    'inet1': poc.devices['HUB2'].wan.inet1,
                    'inet2': poc.devices['HUB2'].wan.inet2,
                    'inet3': poc.devices['HUB2'].wan.inet3,
                    'mpls': poc.devices['HUB2'].wan.mpls1,
                    # 'lan': PE['HUB2'],
                    'lan': segments['HUB1']['DATA'],
                    'loopback': dc_loopbacks['HUB2'],
                }


    datacenters = {
            'west': {
                'first': hub1_,
                'second': hub1_,
            },
            'east': {
                'first': hub2_,
                'second': hub2_,
            },
        }

    rendezvous_points = {}
    if context['multicast']:
        rendezvous_points = {
            'HUB1': '10.200.1.239',
            'HUB2': '10.200.2.239',
        }

        context.update({'rendezvous_points': rendezvous_points})

    #
    # FortiGate Devices

    hub1 = FortiGate(name='HUB1', template_group='DATACENTERS',
                         # lan=PE['HUB1'],
                         lan=segments['HUB1']['DATA'],
                         template_context=context | {'dc_id': 1, 'gps': (48.856614, 2.352222),
                                'region': 'West', 'region_id': 1,
                                'loopback': dc_loopbacks['HUB1'],
                                'datacenter': datacenters,
                                'vrf_segments': segments['HUB1'],
                                })
    hub2 = FortiGate(name='HUB2', template_group='DATACENTERS',
                         # lan=PE['HUB2'],
                         lan=segments['HUB2']['DATA'],
                         template_context=context | {'dc_id': 2, 'gps': (50.1109221, 8.6821267),
                                'region': 'East', 'region_id': 2,
                                'loopback': dc_loopbacks['HUB2'],
                                'datacenter': datacenters,
                                'vrf_segments': segments['HUB2'],
                                })
    br1 = FortiGate(name='BRANCH1', template_group='BRANCHES',
                         lan=segments['BRANCH1']['LAN'],
                         template_context=context | {'branch_id': 1, 'gps': (44.8333, -0.5667),
                                'region': 'West', 'region_id': 1,
                                'loopback': '10.200.1.1',
                                'datacenter': datacenters['west'],
                                 'vrf_segments': segments['BRANCH1'],
                                 })
    br2 = FortiGate(name='BRANCH2', template_group='BRANCHES',
                         lan=segments['BRANCH2']['LAN'],
                         template_context=context | {'branch_id': 2, 'gps': (43.616354, 7.055222),
                                'region': 'West', 'region_id': 1,
                                'loopback': '10.200.1.2',
                                'datacenter': datacenters['west'],
                                 'vrf_segments': segments['BRANCH2'],
                                 })
    br3 = FortiGate(name='BRANCH3', template_group='BRANCHES',
                         lan=segments['BRANCH3']['LAN'],
                         template_context=context | {'branch_id': 3, 'gps': (47.497912, 19.040235),
                                'region': 'East', 'region_id': 2,
                                'loopback': '10.200.2.3',
                                'datacenter': datacenters['east'],
                                 'vrf_segments': segments['BRANCH3'],
                                 })
    br4 = FortiGate(name='BRANCH4', template_group='BRANCHES',
                         lan=segments['BRANCH4']['LAN'],
                         template_context=context | {'branch_id': 4, 'gps': (47.497912, 19.040235),
                                'region': 'East', 'region_id': 2,
                                'loopback': '10.200.2.4',
                                'datacenter': datacenters['east'],
                                 'vrf_segments': segments['BRANCH4'],
                                 })


    devices = {
        'HUB1': hub1,
        'HUB2': hub2,
        'BRANCH1': br1,
        'BRANCH2': br2,
        'BRANCH3': br3,
        'BRANCH4': br4,
        'INFRACOM': FortiGate(name='INFRACOM', template_filename='INFRACOM.conf', template_context=context)
    }

    # Check request, render and deploy configs
    return fpoc.start(poc, devices)