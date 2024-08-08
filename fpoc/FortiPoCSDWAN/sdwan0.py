from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import fpoc
from fpoc import FortiGate, FortiGate_HA, LXC
from fpoc.FortiPoCSDWAN import FortiPoCSDWAN

APPNAME = "fpoc/FortiPoCSDWAN"


def singlehub(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    if poc_id == 5:  # BGP per overlay, FOS 6.2+
        devices, context = singlehub_fos62(request)
    elif poc_id == 8:  # BGP per overlay, FOS 7.0+
        devices, context = singlehub_fos70(request)
    else:
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': 'Unknown POC-ID'})

    # Settings used for HA
    #
    if request.POST.get('HA') == 'FGCP':
        for cluster in (('FGT-A', 'FGT-A_sec'), ('FGT-B', 'FGT-B_sec'), ('FGT-C', 'FGT-C_sec')):  # list of all clusters
            devices[cluster[0]].ha.mode = devices[cluster[1]].ha.mode = FortiGate_HA.Modes.FGCP
            devices[cluster[0]].ha.role = FortiGate_HA.Roles.PRIMARY
            devices[cluster[1]].ha.role = FortiGate_HA.Roles.SECONDARY
            devices[cluster[0]].ha.priority = 200
            devices[cluster[1]].ha.priority = 100
            devices[cluster[0]].ha.group_id = devices[cluster[1]].ha.group_id = 1
            devices[cluster[0]].ha.group_name = devices[cluster[0]].name  # group_name defaults to the device name
            devices[cluster[1]].ha.group_name = devices[cluster[1]].name
            devices[cluster[0]].ha.hbdev = devices[cluster[1]].ha.hbdev = [('port6', 0)]  # heartbeat interfaces
            devices[cluster[0]].ha.sessyncdev = devices[cluster[1]].ha.sessyncdev = [
                'port6']  # session synch interfaces
            devices[cluster[0]].ha.monitordev = devices[cluster[1]].ha.monitordev = ['port1', 'port2',
                                                                                     'port5']  # monitored interfaces

    # The request.POST sends all secondary devices (FGT-A_sec, etc...) for simplicity
    # The request.POST is a read-only QueryDict. So, to avoid configuring unrequested secondary devices I'm removing them
    # from the list of 'devices' (which was also initialized with all devices for simplicity)
    for cluster in (('FGT-A', 'FGT-A_sec'), ('FGT-B', 'FGT-B_sec'), ('FGT-C', 'FGT-C_sec')):  # list of all clusters
        if request.POST.get('HA') == 'standalone':  # No HA = all secondary devices must be removed from the list
            del devices[cluster[1]]
        elif not request.POST.get(cluster[0]):  # this device is not in the list of to-be-configured devices
            del devices[cluster[1]]  # delete the secondary device from the list of devices to be configured

    # Check request, render and deploy configs
    return fpoc.start(request, poc_id, devices, class_=FortiPoCSDWAN)


def singlehub_fos70(request: WSGIRequest) -> tuple:
    context = {
        'remote_internet': request.POST.get('remote_internet'),  # 'none', 'mpls', 'all'
        'vrf_aware_overlay': bool(request.POST.get('vrf_aware_overlay', False)),  # True or False

        # Underlay IPs of the Hub which are used as IPsec remote-gw by the branches
        'hub_inet1': FortiPoCSDWAN.devices['FGT-A'].wan.inet1.subnet + '.3',  # 100.64.11.3
        'hub_inet2': FortiPoCSDWAN.devices['FGT-A'].wan.inet2.subnet + '.3',  # 100.64.12.3
        'hub_mpls': FortiPoCSDWAN.devices['FGT-A'].wan.mpls1.subnet + '.3',  # 10.0.14.3
    }

    devices = {
        'FGT-A': FortiGate(name='FGT-DC', template_group='DATACENTER', template_context={'i': 3, **context}),
        'FGT-A_sec': FortiGate(name='FGT-DC_sec', template_group='Secondary', template_context={'i': 3}),
        'FGT-B': FortiGate(name='FGT-BR1', template_group='BRANCHES', template_context={'i': 1, **context}),
        'FGT-B_sec': FortiGate(name='FGT-BR1_sec', template_group='Secondary', template_context={'i': 1}),
        'FGT-C': FortiGate(name='FGT-BR2', template_group='BRANCHES', template_context={'i': 2, **context}),
        'FGT-C_sec': FortiGate(name='FGT-BR2_sec', template_group='Secondary', template_context={'i': 2}),
    }

    if not context['vrf_aware_overlay']:
        devices['PC_A1'] = LXC(name='DC-server',
                               template_context={'ipmask': '10.1.0.7/24', 'gateway': '10.1.0.1'})
        devices['PC_B1'] = LXC(name='Client-BR1',
                               template_context={'ipmask': '10.0.1.101/24', 'gateway': '10.0.1.1'})
        devices['PC_C1'] = LXC(name='Client-BR2',
                               template_context={'ipmask': '10.0.2.101/24', 'gateway': '10.0.2.1'})
    else:
        devices['PC_A1'] = LXC(name='DC-server',
                               template_context={'vlan_list': [{'vlan':0, 'ipmask': '10.1.0.7/24'},
                                                            {'vlan': 1001, 'ipmask': '10.1.1.7/24'},
                                                            {'vlan': 1002, 'ipmask': '10.1.2.7/24'},
                                                            {'vlan': 1003, 'ipmask': '10.1.3.7/24'},
                                                            ],
                                                 'gateway': '10.1.0.1'})
        devices['PC_B1'] = LXC(name='Client-BR1',
                               template_context={'vlan_list': [{'vlan':0, 'ipmask': '10.0.1.101/24'},
                                                            {'vlan': 1001, 'ipmask': '10.0.11.101/24'},
                                                            {'vlan': 1002, 'ipmask': '10.0.21.101/24'},
                                                            {'vlan': 1003, 'ipmask': '10.0.31.101/24'},
                                                            ],
                                                 'gateway': '10.0.1.1'})
        devices['PC_C1'] = LXC(name='Client-BR2',
                               template_context={'vlan_list': [{'vlan':0, 'ipmask': '10.0.2.101/24'},
                                                            {'vlan': 1001, 'ipmask': '10.0.12.101/24'},
                                                            {'vlan': 1002, 'ipmask': '10.0.22.101/24'},
                                                            {'vlan': 1003, 'ipmask': '10.0.32.101/24'},
                                                            ],
                                                 'gateway': '10.0.2.1'})

    return devices, context


def singlehub_fos62(request: WSGIRequest) -> tuple:
    context = {
        'overlay': request.POST.get('overlay'),  # 'static' or 'mode-cfg'
        'duplicate_paths': request.POST.get('duplicate_paths'), # 'keep_duplicates', 'onnet_pref_spokes', 'offnet_filter_hub'
        'override_with_hub_nexthop': bool(request.POST.get('override_with_hub_nexthop', False)),  # True or False
        'feasible_routes': request.POST.get('feasible_routes'), # 'none', 'rfc1918', 'remote_internet_all', 'remote_internet_mpls'

        # Underlay IPs of the Hub which are used as IPsec remote-gw by the branches
        'hub_inet1': FortiPoCSDWAN.devices['FGT-A'].wan.inet1.subnet + '.3',  # 100.64.11.3
        'hub_inet2': FortiPoCSDWAN.devices['FGT-A'].wan.inet2.subnet + '.3',  # 100.64.12.3
        'hub_lte': FortiPoCSDWAN.devices['FGT-A'].wan.inet1.subnet + '.3',  # 100.64.11.3
        'hub_mpls': FortiPoCSDWAN.devices['FGT-A'].wan.mpls1.subnet + '.3',  # 10.0.14.3
    }

    # Most common set of configuration settings should be:
    #
    # FOS 7.0:
    # - keep duplicates   + no feasible routes
    # - if remote Internet breakout feasible route, need use 'best-fib-match' strategy
    #
    # FOS 6.4:
    # - keep duplicates   + no feasible routes
    # - if remote Internet breakout feasible route, need blackhole route (see my sdwan+advpn 6.4 workshop)
    #
    # FOS 6.2:
    # - off-net filtering + rfc1918/default feasible route                 (override does not apply here)
    # - on-net preference + override    + no feasible route
    # - on-net preference + no override + rfc1918/default feasible route
    #

    # Ideas for automatic config adjustment

    # if context['duplicate_paths'] == 'offnet_filter_hub' and context['feasible_routes'] == 'none':
    #     # feasible routes are mandatory for 'offnet filtering', force 'rfc1918'
    #     context['feasible_routes'] = 'rfc1918'

    # force feasible routes to 'rfc1918' when on-net pref is done and cross-overlay next-hop resolution can happen
    # cross-overlay next-hop resolution = spoke-1 sends traffic over advpn1 due to resolving cross-overlay BGP Next-Hop
    # 10.255.2.x which belongs to advpn2 of spoke-2
    # cross-overlay next-hop resolution should no longer be possible when off-net prefixes are overridden with the
    # Hub's next-hop
    # if context['duplicate_paths'] == 'onnet_pref_spokes' and context['override_with_hub_nexthop'] == False and context['feasible_routes'] == 'none':
    #     # feasible routes are mandatory for 'onnet pref' with cross-overlay shortcut, force 'rfc1918'
    #     context['feasible_routes'] = 'rfc1918'

    # if 'keep duplicates' is desired then there should be no need for feasible routes (AFAIK)
    # or maybe feasible route with 'keep duplicates' are not needed only if cross-overlay shortcut resolution cannot happen
    # for the time being, I'll force feasible route to 'none' for 'keep duplicates' irrespective of 'cross-overlay shortcut resolution'
    # if context['duplicate_paths'] == 'keep_duplicates':
    #     context['feasible_routes'] = 'none'

    # Some options are exclusive

    if context['duplicate_paths'] == 'offnet_filter_hub':
        # There is no possible off-net prefix on a spoke when off-net prefixes are filtered by the Hub
        # So force 'override' to False
        context['override_with_hub_nexthop'] = False

    devices = {
        'FGT-A': FortiGate(name='FGT-DC-3', template_group='FGT-DC', template_context={'i': 3, **context}),
        'FGT-A_sec': FortiGate(name='FGT-DC-3_sec', template_group='Secondary', template_context={'i': 3}),
        'FGT-B': FortiGate(name='FGT-SDW-1', template_group='FGT-SDW', template_context={'i': 1, **context}),
        'FGT-B_sec': FortiGate(name='FGT-SDW-1_sec', template_group='Secondary', template_context={'i': 1}),
        'FGT-C': FortiGate(name='FGT-SDW-2', template_group='FGT-SDW', template_context={'i': 2, **context}),
        'FGT-C_sec': FortiGate(name='FGT-SDW-2_sec', template_group='Secondary', template_context={'i': 2}),

        'PC_A1': LXC(name='DC-server-4', template_context={'ipmask': '192.168.3.4/24', 'gateway': '192.168.3.3'}),
        'PC_B1': LXC(name='Client-11', template_context={'ipmask': '192.168.1.11/24', 'gateway': '192.168.1.1'}),
        'PC_C1': LXC(name='Client-22', template_context={'ipmask': '192.168.2.22/24', 'gateway': '192.168.2.2'}),
    }

    return devices, context
