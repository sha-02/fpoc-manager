from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse

import fpoc
from fpoc.devices import Interface, FortiGate, WAN
from .once import FabricStudioPoCOnce


def poc01(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    Single Hub, Two Branches
    """

    #
    # Create the poc
    #
    poc = FabricStudioPoCOnce(request)

    poc.id = poc_id
    poc.minimum_FOS_version = 8_000_000
    poc.messages = []
    poc.mgmt.vrfid = 0

    #
    # Define devices and rendering context
    #

    context = {
        # From HTML form
        'overlay': 'no_ip',
        'full_mesh_ipsec': False,
        'dualHub_failover': 'lowest-cost',
        'multicast': False,
        'corporate_summary': 'net10',

        # VRF segmentation
        'vrf_aware_overlay': False,
        'vrf_wan': 0,
        'vrf_pe': 0,

        # FMG
        'fortimanager': False,
        'fmg_sn': None,
    }


    #
    # LAN underlays
    #

    LAN = {
        'HUB': Interface(address='10.1.0.1/24', alias='DC'),
        'BRANCH1': Interface(address='10.0.1.1/24', alias='LAN'),
        'BRANCH2': Interface(address='10.0.2.1/24', alias='LAN'),
    }

    dc_loopbacks = {
        'HUB': '10.200.1.251',
    }

    west_dc1_ = {
                    'id': 1,
                    'inet1': poc.devices['HUB'].wan.inet1,
                    'inet2': poc.devices['HUB'].wan.inet2,
                    'mpls': poc.devices['HUB'].wan.mpls1,
                    'lan': LAN['HUB'],
                    'loopback': dc_loopbacks['HUB']
                }


    datacenters = {
            'west': {
                'first': west_dc1_,
                'second': west_dc1_,    # fictitious
            },
        }

    #
    # FortiGate Devices

    west_dc1 = FortiGate(name='HUB', template_group='DATACENTERS',
                         lan=LAN['HUB'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'dc_id': 1, 'gps': (48.856614, 2.352222),
                                'loopback': dc_loopbacks['HUB'],
                                'datacenter': datacenters
                                })
    west_br1 = FortiGate(name='BRANCH1', template_group='BRANCHES',
                         lan=LAN['BRANCH1'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'branch_id': 1, 'gps': (44.8333, -0.5667),
                                'loopback': '10.200.1.1',
                                'datacenter': datacenters['west']
                             })
    west_br2 = FortiGate(name='BRANCH2', template_group='BRANCHES',
                         lan=LAN['BRANCH2'],
                         template_context=context | {'region': 'West', 'region_id': 1, 'branch_id': 2, 'gps': (43.616354, 7.055222),
                                'loopback': '10.200.1.2',
                                'datacenter': datacenters['west']
                                 })

    devices = {
        'HUB': west_dc1,
        'BRANCH1': west_br1,
        'BRANCH2': west_br2,
    }

    # Check request, render and deploy configs
    return fpoc.start(poc, devices)