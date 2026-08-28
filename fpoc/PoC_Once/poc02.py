from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
import copy

from fpoc.deploy import start
from fpoc.devices import Interface, FortiGate, FortiGate_HA, LAN
from .once import FabricStudioPoCOnce, AgoraPoCOnce


def poc02(request: WSGIRequest, poc_id: int, execution_environment: str = "FabricStudio", **kwargs) -> HttpResponse:
    """
    FOS 7.6.7
    Dual Region, Single Hub per Region, 4x Branches (2x BR per Region)
    3x VRFs (Data, Voice, Video): IPv4/VPNv4 & IPv6/VPNv6
    multicast IPv4 in VRFs
    EVPN: two extended LANs between BR1<->BR2 in Region1 and BR3<->BR4 in Region2
    No local breakout, only overlay traffic

    execution_environment = 'FabricStudio' or 'Agora'
    kwargs = dict() which may be passed by the urlpattern caller path(...) in 'urls' files
    """

    #
    # Create the poc
    #
    if execution_environment == "Agora":
        poc = AgoraPoCOnce(request)
    else:
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
        'HUB1': LAN(
            DATA= Interface(address='192.168.1.11/31', alias='DATA', vrfid=context['vrf_data']).update(poc.devices['HUB1'].segments.lan2),
            VOICE= Interface(address='192.168.1.12/31', alias='VOICE', vrfid=context['vrf_voice']).update(poc.devices['HUB1'].segments.lan3),
            VIDEO= Interface(address='192.168.1.14/31', alias='VIDEO', vrfid=context['vrf_video']).update(poc.devices['HUB1'].segments.lan4),
        ),
        'HUB2': LAN(
            DATA= Interface(address='192.168.2.11/31', alias='DATA', vrfid=context['vrf_data']).update(poc.devices['HUB2'].segments.lan2),
            VOICE= Interface(address='192.168.2.12/31', alias='VOICE', vrfid=context['vrf_voice']).update(poc.devices['HUB2'].segments.lan3),
            VIDEO= Interface(address='192.168.2.14/31', alias='VIDEO', vrfid=context['vrf_video']).update(poc.devices['HUB2'].segments.lan4),
        ),
        'BRANCH1': LAN(
            LAN= Interface(address='10.1.10.1/24', alias='LAN_DATA', vrfid=context['vrf_data']).update(poc.devices['BRANCH1'].segments.lan1),
            LAN_VOICE= Interface(address='10.1.11.1/24', alias='LAN_VOICE', vrfid=context['vrf_voice']).update(poc.devices['BRANCH1'].segments.lan2),
            LAN_VIDEO= Interface(address='10.1.12.1/24', alias='LAN_VIDEO', vrfid=context['vrf_video']).update(poc.devices['BRANCH1'].segments.lan3),
        ),
        'BRANCH2': LAN(
            LAN= Interface(address='10.2.10.1/24', alias='LAN_DATA', vrfid=context['vrf_data']).update(poc.devices['BRANCH2'].segments.lan1),
            LAN_VOICE= Interface(address='10.2.11.1/24', alias='LAN_VOICE', vrfid=context['vrf_voice']).update(poc.devices['BRANCH2'].segments.lan2),
            LAN_VIDEO= Interface(address='10.2.12.1/24', alias='LAN_VIDEO', vrfid=context['vrf_video']).update(poc.devices['BRANCH2'].segments.lan3),
        ),
        'BRANCH3': LAN(
            LAN= Interface(address='10.3.10.1/24', alias='LAN_DATA', vrfid=context['vrf_data']).update(poc.devices['BRANCH3'].segments.lan1),
            LAN_VOICE= Interface(address='10.3.11.1/24', alias='LAN_VOICE', vrfid=context['vrf_voice']).update(poc.devices['BRANCH3'].segments.lan2),
            LAN_VIDEO= Interface(address='10.3.12.1/24', alias='LAN_VIDEO', vrfid=context['vrf_video']).update(poc.devices['BRANCH3'].segments.lan3),
        ),
        'BRANCH4': LAN(
            LAN= Interface(address='10.4.10.1/24', alias='LAN_DATA', vrfid=context['vrf_data']).update(poc.devices['BRANCH4'].segments.lan1),
            LAN_VOICE= Interface(address='10.4.11.1/24', alias='LAN_VOICE', vrfid=context['vrf_voice']).update(poc.devices['BRANCH4'].segments.lan2),
            LAN_VIDEO= Interface(address='10.4.12.1/24', alias='LAN_VIDEO', vrfid=context['vrf_video']).update(poc.devices['BRANCH4'].segments.lan3),
        ),
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
        'lan': segments['HUB1'].DATA,
        'loopback': dc_loopbacks['HUB1'],
    }

    hub2_ = {
        'id': 2,
        'inet1': poc.devices['HUB2'].wan.inet1,
        'inet2': poc.devices['HUB2'].wan.inet2,
        'inet3': poc.devices['HUB2'].wan.inet3,
        'mpls': poc.devices['HUB2'].wan.mpls1,
        'lan': segments['HUB1'].DATA,
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
                     # HA=FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, role=FortiGate_HA.Roles.PRIMARY,
                     #                 group_id=91, group_name="HUB1", priority=129),
                     lan=segments['HUB1'].DATA,
                     template_context=context | {'dc_id': 1, 'gps': (48.856614, 2.352222),
                                                 'region': 'West', 'region_id': 1,
                                                 'loopback': dc_loopbacks['HUB1'],
                                                 'datacenter': datacenters,
                                                 'vrf_segments': segments['HUB1'],
                                                 })
    hub1_sec = FortiGate(name='HUB1-B', template_group='DATACENTERS',
                         HA=FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, role=FortiGate_HA.Roles.SECONDARY,
                                         group_id=91, group_name="HUB1", priority=127))

    hub2 = FortiGate(name='HUB2', template_group='DATACENTERS',
                     lan=segments['HUB2'].DATA,
                     template_context=context | {'dc_id': 2, 'gps': (50.1109221, 8.6821267),
                                                 'region': 'East', 'region_id': 2,
                                                 'loopback': dc_loopbacks['HUB2'],
                                                 'datacenter': datacenters,
                                                 'vrf_segments': segments['HUB2'],
                                                 })
    br1 = FortiGate(name='BRANCH1', template_group='BRANCHES',
                    HA=FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, role=FortiGate_HA.Roles.PRIMARY,
                                    group_id=1, group_name="BRANCH1", priority=129),
                    lan=segments['BRANCH1'].LAN,
                    template_context=context | {'branch_id': 1, 'gps': (44.8333, -0.5667),
                                                'region': 'West', 'region_id': 1,
                                                'loopback': '10.200.1.1',
                                                'datacenter': datacenters['west'],
                                                'vrf_segments': segments['BRANCH1'],
                                                })
    br1_sec = FortiGate(name='BRANCH1-B', template_group='BRANCHES',
                        HA=FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, role=FortiGate_HA.Roles.SECONDARY,
                                        group_id=1, group_name="BRANCH1", priority=127))

    br2 = FortiGate(name='BRANCH2', template_group='BRANCHES',
                    lan=segments['BRANCH2'].LAN,
                    template_context=context | {'branch_id': 2, 'gps': (43.616354, 7.055222),
                                                'region': 'West', 'region_id': 1,
                                                'loopback': '10.200.1.2',
                                                'datacenter': datacenters['west'],
                                                'vrf_segments': segments['BRANCH2'],
                                                })
    br3 = FortiGate(name='BRANCH3', template_group='BRANCHES',
                    lan=segments['BRANCH3'].LAN,
                    template_context=context | {'branch_id': 3, 'gps': (47.497912, 19.040235),
                                                'region': 'East', 'region_id': 2,
                                                'loopback': '10.200.2.3',
                                                'datacenter': datacenters['east'],
                                                'vrf_segments': segments['BRANCH3'],
                                                })
    br4 = FortiGate(name='BRANCH4', template_group='BRANCHES',
                    lan=segments['BRANCH4'].LAN,
                    template_context=context | {'branch_id': 4, 'gps': (47.497912, 19.040235),
                                                'region': 'East', 'region_id': 2,
                                                'loopback': '10.200.2.4',
                                                'datacenter': datacenters['east'],
                                                'vrf_segments': segments['BRANCH4'],
                                                })


    if execution_environment == "Agora":
        context_INFRACOM_execution_environment = {
            'INFRACOM_VLAN_IDs': 'INFRACOM.agora.conf',
            'HUB1_segments': segments['HUB1'],
            'HUB2_segments': segments['HUB2'],
        }
    else:
        context_INFRACOM_execution_environment = {
            'INFRACOM_VLAN_IDs': 'INFRACOM.studio.conf',
        }


    devices = {
        'HUB1': hub1,
        # 'HUB1-B': hub1_sec,
        'HUB2': hub2,
        'BRANCH1': br1,
        'BRANCH1-B': br1_sec,
        'BRANCH2': br2,
        'BRANCH3': br3,
        'BRANCH4': br4,
        'INFRACOM': FortiGate(name='INFRACOM', template_filename='INFRACOM.conf',
                              template_context=context|context_INFRACOM_execution_environment)
    }

    # Check request, render and deploy configs
    return start(poc, devices)