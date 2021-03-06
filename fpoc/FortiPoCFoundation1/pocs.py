import threading

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse

from collections import namedtuple

import fpoc
import fpoc.fortios as fortios
from fpoc import FortiGate, FortiGate_HA, LXC, FortiManager, Vyos
from fpoc.FortiPoCFoundation1 import FortiPoCFoundation1
import fpoc.ansible as ansible

APPNAME = "fpoc/FortiPoCFoundation1"

Status = namedtuple('Status', 'is_valid is_invalid message')


def upgrade(request: WSGIRequest) -> HttpResponse:
    """
    """

    fos_version_target = request.POST.get('targetedFOSversion')
    if not fos_version_target:
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': 'FortiOS version must be provided'})

    # the intersection of the keys of request.POST dict and the foundation1 dict keys produces the keys of each
    # device to be upgraded
    fortigates = FortiPoCFoundation1.devices_of_type(FortiGate)  # All FortiGate devices
    fortigates = sorted(list(request.POST.keys() & fortigates.keys()))

    if request.POST.get('previewOnly'):
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Upgrade', 'header': 'Upgrade preview', 'message': fortigates})

    def _upgrade_fgt(device: FortiGate, fos_version_target: str, lock: threading.Lock):
        fortios.prepare_api(device)  # create API admin and key if needed
        fortios.update_fortios_version(device, fos_version_target, lock)  # Upgrade/Downgrade FortiGate

    poc = FortiPoCFoundation1(request, fpoc_devnames=fortigates)
    threads = list()
    for fgt in poc:
        print(f'{fgt.name} : Upgrading to FortiOS', request.POST.get('targetedFOSversion'), ' ...')
        thread = threading.Thread(target=_upgrade_fgt, args=(fgt, fos_version_target, poc.lock))
        threads.append(thread)
        thread.start()

    for index, thread in enumerate(threads):
        thread.join()

    return render(request, f'{APPNAME}/message.html',
                  {'title': 'Upgrade', 'header': 'Upgrade status', 'message': fortigates})


def poweron(request: WSGIRequest) -> HttpResponse:
    """
    """
    fundation1_devices = FortiPoCFoundation1.devices_of_type(FortiGate)  # All FortiGate devices
    fundation1_devices.update(FortiPoCFoundation1.devices_of_type(LXC))  # + all LXC devices
    fundation1_devices.update(FortiPoCFoundation1.devices_of_type(Vyos))  # + all VyOS devices

    # the intersection of the keys of request.POST dict and the fundation1 dict keys produces the keys of each
    # device to be powered on
    devices_to_start = sorted(list(request.POST.keys() & fundation1_devices.keys()))

    if request.POST.get('previewOnly'):
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Power-On', 'header': 'Power-On preview', 'message': devices_to_start})

    # Create an FPOC instance because we need to know the IP@ to be used to reach the FPOC
    poc = FortiPoCFoundation1(request)

    # TODO: admin & pwd should be stored in DB so that it can be customized per FortiPoC (like WAN_CTRL)
    _, result = ansible.poweron_devices(devices_to_start, host=poc.ip, admin='admin', pwd='')
    result = '<pre> ' + result + ' </pre>'

    return render(request, f'{APPNAME}/message.html',
                  {'title': 'Power-On', 'header': 'Power-On status', 'message': result})


def bootstrap(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    # Check the request
    if request.POST.get('targetedFOSversion') == '':
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': 'The FortiOS version must be specified'})

    devices = FortiPoCFoundation1.devices_of_type(FortiGate)  # All FortiGate devices

    for fpoc_devname, device in devices.items():
        device.template_filename = request.POST.get('targetedFOSversion') + '.conf'  # e.g. '6.4.6.conf'

        device.template_context = {'name': fpoc_devname, 'mgmt': FortiPoCFoundation1.devices[fpoc_devname].mgmt}
        if bool(request.POST.get('WAN_underlays', False)) and device.wan is not None:
            device.template_context['WAN_underlays'] = True
            device.template_context['wan'] = device.wan
            device.template_context['ip_lastbyte'] = device.offset + 1
        else:
            device.template_context['WAN_underlays'] = False

        if request.POST.get('HA') == 'FGCP':
            device.ha = FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, group_id=1, group_name=fpoc_devname,
                                     hbdev=[('port6', 0)], sessyncdev=['port6'],
                                     monitordev=['port1', 'port2', 'port5'], priority=128)
            if fpoc_devname in ('FGT-A_sec', 'FGT-B_sec', 'FGT-C_sec', 'FGT-D_sec'):
                device.ha.role = FortiGate_HA.Roles.SECONDARY
            else:
                device.ha.role = FortiGate_HA.Roles.PRIMARY

    devices['FMG'] = FortiManager(name='FMG')

    # Render and deploy the configs
    return start(request, poc_id, devices)


def sdwan_simple(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    context = {
        # Underlay IP@ of the Hub for IPsec VPN on Branches ('set remote-gw x.x.x.x')
        'hub': FortiPoCFoundation1.devices['FGT-C'].wan.inet1.subnet + '.1',  # 100.64.31.1
    }

    devices = {
        'FGT-A': FortiGate(name='FGT-A', template_group='BRANCHES',
                           template_context={'i': 1, 'overlay': '10.255', **context}),
        'FGT-B': FortiGate(name='FGT-B', template_group='BRANCHES',
                           template_context={'i': 2, 'overlay': '10.254', **context}),
        'FGT-C': FortiGate(name='FGT-DC', template_group='DATACENTER'),

        'PC_A1': LXC(name='PC-A1', template_context={'ipmask': '192.168.1.1/24', 'gateway': '192.168.1.254'}),
        'PC_A2': LXC(name='PC-A2', template_context={'ipmask': '192.168.1.2/24', 'gateway': '192.168.1.254'}),
        'PC_B1': LXC(name='PC-B1', template_context={'ipmask': '192.168.2.1/24', 'gateway': '192.168.2.254'}),
        'PC_B2': LXC(name='PC-B2', template_context={'ipmask': '192.168.2.2/24', 'gateway': '192.168.2.254'}),
        'PC_C1': LXC(name='DC-Server', template_context={'ipmask': '192.168.0.100/24', 'gateway': '192.168.0.254'}),
    }

    # Check request, render and deploy configs
    return start(request, poc_id, devices)


def vpn_site2site(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    context = {
        'vpn': request.POST.get('vpn'),  # 'ipsec', 'gre', ...
        'routing': request.POST.get('routing'),  # 'static', 'ospf', 'ibgp', ...
        'ike': request.POST.get('ike'),  # 1 or 2
        'ipsec_phase1': request.POST.get('ipsec_phase1'),  # 'static2static', 'static2dialup'

        # Used as 'remote-gw' for IPsec tunnels
        'fgta_inet1': FortiPoCFoundation1.devices['FGT-A'].wan.inet1.subnet + '.1',  # 100.64.11.1
        'fgta_inet2': FortiPoCFoundation1.devices['FGT-A'].wan.inet2.subnet + '.1',  # 100.64.11.1
        'fgtb_inet1': FortiPoCFoundation1.devices['FGT-B'].wan.inet1.subnet + '.2',  # 100.64.21.2
        'fgtb_inet2': FortiPoCFoundation1.devices['FGT-B'].wan.inet2.subnet + '.2',  # 100.64.22.2
    }

    # If IPsec VPN with 'static2dialup' is selected then only static routing is possible
    if context['vpn'] == 'ipsec' and context['ipsec_phase1'] == 'static2dialup':
        context['routing'] = 'static'
    # 'static2dialup' only applies to pure IPsec VPN, not GRE-IPsec, not IP-IP-IPsec, etc...
    if context['ipsec_phase1'] == 'static2dialup' and context['vpn'] != 'ipsec':
        context['ipsec_phase1'] = 'static2static'  # force to 'static2static' if it's not pure IPsec VPN

    # List of all devices for this Scenario
    devices = {
        'FGT-A': FortiGate(name='FGT-A', template_group='SITES', template_context={'i': 1, **context}),
        'FGT-B': FortiGate(name='FGT-B', template_group='SITES', template_context={'i': 2, **context}),
        'PC_A1': LXC(name='PC-A1', template_context={'ipmask': '192.168.1.1/24', 'gateway': '192.168.1.254'}),
        'PC_A2': LXC(name='PC-A11', template_context={'ipmask': '192.168.11.1/24', 'gateway': '192.168.11.254'}),
        'PC_B1': LXC(name='PC-B2', template_context={'ipmask': '192.168.2.1/24', 'gateway': '192.168.2.254'}),
        'PC_B2': LXC(name='PC-B22', template_context={'ipmask': '192.168.22.1/24', 'gateway': '192.168.22.254'}),
    }

    # Check request, render and deploy configs
    return start(request, poc_id, devices)


def vpn_dialup(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    context = {
        'ike': request.POST.get('ike'),  # 1 or 2
        'overlay': request.POST.get('overlay'),  # 'static' or 'mode-cfg' or 'unnumbered'
        'routing': request.POST.get('routing'),  # 'ike-routing', 'modecfg-routing', 'ospf', 'ibgp', 'ebgp',
        # 'ibgp-confederation'
        'advpn': bool(request.POST.get('advpn', False)),  # True or False
        'nat_hub': request.POST.get('Hub_NAT'),  # Type of NAT for Hub = 'None', 'DNAT'

        # Hub is FGT-A from FortiPoC "Fundation1"
        'hub': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.1',  # IP when not DNATed: 198.51.100.1
        'hub_dnat': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.201',  # IP when DNATed: 198.51.100.201
    }

    # Some options are exclusive
    if context['routing'] == 'ike-routing':
        context['overlay'] = 'unnumbered'
        context['advpn'] = False

    if context['routing'] == 'modecfg-routing':
        context['overlay'] = 'mode-cfg'
        context['advpn'] = False

    if context['routing'] in ('ebgp', 'ibgp-confederation') and context['overlay'] == 'mode-cfg':
        # Each site has its own ASN (for 'ebgp') or its own sub-confed (for 'ibgp-confederation')
        # So the Hub cannot use dynamic peering, it must use static peering
        # mode-cfg cannot therefore be used since the Spokes' overlay-ip is not predictable with mode-cfg
        context['overlay'] = 'static'

    if context['routing'] in ('ebgp', 'ibgp-confederation') and context['overlay'] == 'unnumbered':
        # Unnumbered tunnels on Hub and Spokes is possible with BGP
        # BGP must be bound on loopbacks and 'exchange-interface-ip' is used to exchange the loopback IP addresses
        # Generating this config is not yet supported so, for the time being, overlay is forced to 'static'
        context['overlay'] = 'static'

    if context['routing'] == 'ospf' and context['overlay'] == 'unnumbered':
        context['overlay'] = 'mode-cfg'  # An overlay-IP is mandatory for OSPF. Let's force to 'mode-cfg'.

    devices = {
        'FGT-A': FortiGate(name='Hub', template_group='Hubs',
                           template_context={**context, 'nat': request.POST.get('Hub_NAT')}),
        'FGT-B': FortiGate(name='Spoke01', template_group='Spokes',  # Type of NAT: 'None', 'SNAT', 'DNAT'
                           template_context={'i': 1, **context, 'nat': request.POST.get('Spoke01_NAT')}),
        'FGT-C': FortiGate(name='Spoke02', template_group='Spokes',
                           template_context={'i': 2, **context, 'nat': request.POST.get('Spoke02_NAT')}),
        'FGT-D': FortiGate(name='Spoke03', template_group='Spokes',
                           template_context={'i': 3, **context, 'nat': request.POST.get('Spoke03_NAT')}),

        'PC_A1': LXC(name='PC-Hub', template_context={'ipmask': '192.168.0.1/24', 'gateway': '192.168.0.254'}),
        'PC_B1': LXC(name='PC-1', template_context={'ipmask': '192.168.1.1/24', 'gateway': '192.168.1.254'}),
        'PC_C1': LXC(name='PC-2', template_context={'ipmask': '192.168.2.1/24', 'gateway': '192.168.2.254'}),
        'PC_D1': LXC(name='PC-3', template_context={'ipmask': '192.168.3.1/24', 'gateway': '192.168.3.254'}),
    }

    # Check request, render and deploy configs
    return start(request, poc_id, devices)


def vpn_dualhub_singletunnel(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    context = {
        'mode': request.POST.get('mode'),  # 'active_passive' or 'active_active'
        # TODO: active_active configuration is not done in config templates
        'hub1': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.1',  # 198.51.100.1
        'hub2': FortiPoCFoundation1.devices['FGT-A_sec'].wan.inet.subnet + '.2',  # 198.51.100.2
    }

    devices = {
        'FGT-A': FortiGate(name='Hub-1', template_group='Hubs', template_context={**context}),
        'FGT-A_sec': FortiGate(name='Hub-2', template_group='Hubs', template_context={**context}),
        'ISFW-A': FortiGate(name='ISFW', template_context={**context}),
        'FGT-B': FortiGate(name='Spoke1', template_group='Spokes', template_context={'i': 3, **context}),
        'FGT-C': FortiGate(name='Spoke2', template_group='Spokes', template_context={'i': 4, **context}),

        'PC_A1': LXC(name='PC-Hub1', template_context={'ipmask': '192.168.1.11/24', 'gateway': '192.168.1.1'}),
        'PC_A2': LXC(name='PC-Hub2', template_context={'ipmask': '192.168.2.22/24', 'gateway': '192.168.2.1'}),
        'PC_B1': LXC(name='PC-1', template_context={'ipmask': '192.168.3.33/24', 'gateway': '192.168.3.1'}),
        'PC_C1': LXC(name='PC-2', template_context={'ipmask': '192.168.4.44/24', 'gateway': '192.168.4.1'}),
    }

    # device_dependencies = {
    #     'FGT-A': ('PC_A1', 'PC_A2'),
    #     'FGT-A_sec': ('PC_A1', 'PC_A2'),
    #     'FGT-B': ('PC_B1',),
    #     'FGT-C': ('PC_C1',)
    # }

    # Check request, render and deploy configs
    return start(request, poc_id, devices)


def sdwan_advpn_singlehub(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    if poc_id == 5:  # BGP per overlay, FOS 6.2+
        devices, context = sdwan_advpn_singlehub_fos62(request)
    elif poc_id == 8:  # BGP per overlay, FOS 7.0+
        devices, context = sdwan_advpn_singlehub_fos70(request)
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
    return start(request, poc_id, devices)


def sdwan_advpn_singlehub_fos70(request: WSGIRequest) -> tuple:
    context = {
        'remote_internet': request.POST.get('remote_internet'),  # 'none', 'mpls', 'all'
        'vrf_aware_overlay': bool(request.POST.get('vrf_aware_overlay', False)),  # True or False

        # Underlay IPs of the Hub which are used as IPsec remote-gw by the branches
        'hub_inet1': FortiPoCFoundation1.devices['FGT-A'].wan.inet1.subnet + '.3',  # 100.64.11.3
        'hub_inet2': FortiPoCFoundation1.devices['FGT-A'].wan.inet2.subnet + '.3',  # 100.64.12.3
        'hub_mpls': FortiPoCFoundation1.devices['FGT-A'].wan.mpls1.subnet + '.3',  # 10.0.14.3
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
                               template_context={'devlist': [{'vlan':0, 'ipmask': '10.1.0.7/24'},
                                                            {'vlan': 1001, 'ipmask': '10.1.1.7/24'},
                                                            {'vlan': 1002, 'ipmask': '10.1.2.7/24'},
                                                            {'vlan': 1003, 'ipmask': '10.1.3.7/24'},
                                                            ],
                                                 'gateway': '10.1.0.1'})
        devices['PC_B1'] = LXC(name='Client-BR1',
                               template_context={'devlist': [{'vlan':0, 'ipmask': '10.0.1.101/24'},
                                                            {'vlan': 1001, 'ipmask': '10.0.11.101/24'},
                                                            {'vlan': 1002, 'ipmask': '10.0.21.101/24'},
                                                            {'vlan': 1003, 'ipmask': '10.0.31.101/24'},
                                                            ],
                                                 'gateway': '10.0.1.1'})
        devices['PC_C1'] = LXC(name='Client-BR2',
                               template_context={'devlist': [{'vlan':0, 'ipmask': '10.0.2.101/24'},
                                                            {'vlan': 1001, 'ipmask': '10.0.12.101/24'},
                                                            {'vlan': 1002, 'ipmask': '10.0.22.101/24'},
                                                            {'vlan': 1003, 'ipmask': '10.0.32.101/24'},
                                                            ],
                                                 'gateway': '10.0.2.1'})

    return devices, context


def sdwan_advpn_singlehub_fos62(request: WSGIRequest) -> tuple:
    context = {
        'overlay': request.POST.get('overlay'),  # 'static' or 'mode-cfg'
        'duplicate_paths': request.POST.get('duplicate_paths'), # 'keep_duplicates', 'onnet_pref_spokes', 'offnet_filter_hub'
        'override_with_hub_nexthop': bool(request.POST.get('override_with_hub_nexthop', False)),  # True or False
        'feasible_routes': request.POST.get('feasible_routes'), # 'none', 'rfc1918', 'remote_internet_all', 'remote_internet_mpls'

        # Underlay IPs of the Hub which are used as IPsec remote-gw by the branches
        'hub_inet1': FortiPoCFoundation1.devices['FGT-A'].wan.inet1.subnet + '.3',  # 100.64.11.3
        'hub_inet2': FortiPoCFoundation1.devices['FGT-A'].wan.inet2.subnet + '.3',  # 100.64.12.3
        'hub_lte': FortiPoCFoundation1.devices['FGT-A'].wan.inet1.subnet + '.3',  # 100.64.11.3
        'hub_mpls': FortiPoCFoundation1.devices['FGT-A'].wan.mpls1.subnet + '.3',  # 10.0.14.3
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


def sdwan_advpn_dualdc(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    context = {
        # From HTML form
        'remote_internet': request.POST.get('remote_internet'),  # 'none', 'mpls', 'all'
        'bidir_sdwan': request.POST.get('bidir_sdwan'),  # 'none', 'route_tag', 'route_priority'
        'cross_region_advpn': bool(request.POST.get('cross_region_advpn', False)),  # True or False

        # DataCenters info used:
        # - as IPsec remote-gw IP@ by the Branches (inet1/inet2/mpls)
        # - as underlay interfaces IP@ by DCs (inet1/inet2/mpls)
        # - for networkid computation of Edge IPsec tunnels (id)
        'datacenter': {
            'west': {
                'first': {
                    'id': 1,
                    'inet1': FortiPoCFoundation1.devices['FGT-A'].wan.inet1.subnet + '.1',  # 100.64.11.1
                    'inet2': FortiPoCFoundation1.devices['FGT-A'].wan.inet2.subnet + '.1',  # 100.64.12.1
                    'mpls': FortiPoCFoundation1.devices['FGT-A'].wan.mpls1.subnet + '.1',  # 10.0.14.1
                },
                'second': {
                    'id': 2,
                    'inet1': FortiPoCFoundation1.devices['FGT-B'].wan.inet1.subnet + '.2',  # 100.64.21.2
                    'inet2': FortiPoCFoundation1.devices['FGT-B'].wan.inet2.subnet + '.2',  # 100.64.22.2
                    'mpls': FortiPoCFoundation1.devices['FGT-B'].wan.mpls1.subnet + '.2',  # 10.0.24.2
                },
            },
            'east': {
                'first': {
                    'id': 3,
                    'inet1': FortiPoCFoundation1.devices['FGT-B_sec'].wan.inet1.subnet + '.3',  # 100.64.21.3
                    'inet2': FortiPoCFoundation1.devices['FGT-B_sec'].wan.inet2.subnet + '.3',  # 100.64.22.3
                    'mpls': FortiPoCFoundation1.devices['FGT-B_sec'].wan.mpls1.subnet + '.3',  # 10.0.24.3
                },
                'second': {  # Fictitious second DC for East region
                    'id': 4,
                    'inet1': FortiPoCFoundation1.devices['FGT-B_sec'].wan.inet1.subnet + '.4',  # 100.64.21.4
                    'inet2': FortiPoCFoundation1.devices['FGT-B_sec'].wan.inet2.subnet + '.4',  # 100.64.22.4
                    'mpls': FortiPoCFoundation1.devices['FGT-B_sec'].wan.mpls1.subnet + '.4',  # 10.0.24.4
                }
            }
        }
    }

    if poc_id == 10:  # BGP on loopback design -- New IP schema (summarizable) is used for East region of this PoC
        # TODO: configure django jinja2 to use Ansible filter ipaddr instead of this 'lan' dictionnary
        # https://ansible-docs.readthedocs.io/zh/stable-2.0/rst/playbooks_filters_ipaddr.html
        # https://github.com/ansible-collections/ansible.netcommon
        # https://stackoverflow.com/questions/49903636/how-to-use-pip-installed-jinja2-filters-in-python
        # https://gist.github.com/ktbyers/bdba984447636d5ac4e3d93011a861ad
        # https://stackoverflow.com/questions/49903636/how-to-use-pip-installed-jinja2-filters-in-python
        # https://stackoverflow.com/questions/49903636/how-to-use-pip-installed-jinja2-filters-in-python
        # https://stackoverflow.com/questions/68440946/ansible-filters-ipaddr-in-python
        # https://blog.networktocode.com/post/adding-jinja2-filters-in-nautobot-golden-config/
        west_dc1 = FortiGate(name='WEST-DC1', template_group='DATACENTERS', template_context={'region': 'West', 'region_id': 1, 'dc_id': 1, 'lan': {'ip': '10.1.0.1', 'subnet': '10.1.0.0', 'mask': '255.255.255.0'}, **context})
        west_dc2 = FortiGate(name='WEST-DC2', template_group='DATACENTERS', template_context={'region': 'West', 'region_id': 1, 'dc_id': 2, 'lan': {'ip': '10.2.0.1', 'subnet': '10.2.0.0', 'mask': '255.255.255.0'}, **context})
        west_br1 = FortiGate(name='WEST-BR1', template_group='BRANCHES', template_context={'region': 'West', 'region_id': 1, 'branch_id': 1, 'lan': {'ip': '10.0.1.1', 'subnet': '10.0.1.0', 'mask': '255.255.255.0'}, **context})
        west_br2 = FortiGate(name='WEST-BR2', template_group='BRANCHES', template_context={'region': 'West', 'region_id': 1, 'branch_id': 2, 'lan': {'ip': '10.0.2.1', 'subnet': '10.0.2.0', 'mask': '255.255.255.0'}, **context})
        east_dc = FortiGate(name='EAST-DC1', template_group='DATACENTERS', template_context={'region': 'East', 'region_id': 2, 'dc_id': 1, 'lan': {'ip': '10.4.0.1', 'subnet': '10.4.0.0', 'mask': '255.255.255.0'}, **context})
        east_br = FortiGate(name='EAST-BR1', template_group='BRANCHES', template_context={'region': 'East', 'region_id': 2, 'branch_id': 1, 'lan': {'ip': '10.4.1.1', 'subnet': '10.4.1.0', 'mask': '255.255.255.0'}, **context})
        lxc_east_dc = LXC(name='PC-E-DC1', template_context={'ipmask': '10.4.0.7/24', 'gateway': '10.4.0.1'})
        lxc_east_br = LXC(name='PC-E-BR1', template_context={'ipmask': '10.4.1.101/24', 'gateway': '10.4.1.1'})
    else:  # BGP per overlay design with non-summarizable IP schema for East region
        west_dc1 = FortiGate(name='WEST-DC1', template_group='DATACENTERS', template_context={'dc_id': 1, 'region': 'West', **context})
        west_dc2 = FortiGate(name='WEST-DC2', template_group='DATACENTERS', template_context={'dc_id': 2, 'region': 'West', **context})
        west_br1 = FortiGate(name='WEST-BR1', template_group='BRANCHES', template_context={'branch_id': 1, 'region': 'West', **context})
        west_br2 = FortiGate(name='WEST-BR2', template_group='BRANCHES', template_context={'branch_id': 2, 'region': 'West', **context})
        east_dc = FortiGate(name='EAST-DC3', template_group='DATACENTERS', template_context={'dc_id': 3, 'region': 'East', **context})
        east_br = FortiGate(name='EAST-BR3', template_group='BRANCHES', template_context={'branch_id': 3, 'region': 'East', **context})
        lxc_east_dc = LXC(name='PC-E-DC3', template_context={'ipmask': '10.3.0.7/24', 'gateway': '10.3.0.1'})
        lxc_east_br = LXC(name='PC-E-BR3', template_context={'ipmask': '10.0.3.101/24', 'gateway': '10.0.3.1'})

    devices = {
        'FGT-A': west_dc1,
        'FGT-B': west_dc2,
        'FGT-B_sec': east_dc,
        'FGT-C': west_br1,
        'FGT-D': west_br2,
        'FGT-D_sec': east_br,
        'FMG': FortiManager(name='FMG'),

        'PC_A1': LXC(name='PC-W-DC1', template_context={'ipmask': '10.1.0.7/24', 'gateway': '10.1.0.1'}),
        'PC_B1': LXC(name='PC-W-DC2', template_context={'ipmask': '10.2.0.7/24', 'gateway': '10.2.0.1'}),
        'PC_B2': lxc_east_dc,
        'PC_C1': LXC(name='PC-W-BR1', template_context={'ipmask': '10.0.1.101/24', 'gateway': '10.0.1.1'}),
        'PC_D1': LXC(name='PC-W-BR2', template_context={'ipmask': '10.0.2.101/24', 'gateway': '10.0.2.1'}),
        'PC_D2': lxc_east_br,
    }

    # Check request, render and deploy configs
    return start(request, poc_id, devices)


def inspect(request: WSGIRequest) -> Status:
    """
    """
    import ipaddress

    for ipaddr in (request.POST.get('fpocIP'),):
        if ipaddr:
            # Ensure a valid IP address is provided
            try:
                ipaddress.ip_address(ipaddr)  # throws an exception if the IP address is not valid
            except:
                return Status(False, True, f"This is not a valid IP address: {ipaddr}")

    if request.POST.get('previewOnly') and not request.POST.get('targetedFOSversion'):
        return Status(False, True, 'FOS version must be specified when preview-only is selected')

    return Status(True, False, 'request is valid')


def start(request: WSGIRequest, poc_id: int, devices: dict) -> HttpResponse:
    if inspect(request).is_invalid:
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': inspect(request).message})

    # Create the list of devices which must be used for this PoC

    # the intersection of the keys of request.POST dict and the keys of 'devices' dict produces the keys of each
    # device to be used for this poc.
    fpoc_devnames = request.POST.keys() & devices.keys()

    # # Delete devices from 'devices' which do not need to be started
    # # +--> do not use dict comprehension because it creates an unordered list of devices due to using set()
    for fpoc_devname in list(devices.keys()):  # use list of keys() otherwise exception raised bcse
        # the dict changes size during iteration
        if fpoc_devname not in fpoc_devnames:
            del (devices[fpoc_devname])  # this device was not requested to be started for this PoC

    status_devices = fpoc.start(request, poc=FortiPoCFoundation1(request=request, poc_id=poc_id, devices=devices))

    #  For FortiManager provisioning templates: generate the Jinja dict to import into FMG
    #
    fortimanager = ''
    if request.POST.get('FMG'):
        # Only keep FortiGates, skip other devices (LXC, VyOS, ...)
        status_fortigates = [device for device in status_devices if device['context'].get('fos_version') is not None]

        # Create a dictionary of the form:  { 'fgt1_name': 'fgt1_context_dict', 'fgt2_name': 'fgt2_context_dict', ...}
        # Then serialize the contexts in JSON so that they can be used as a Jinja variable
        # Problem with context objects like 'HA' and 'Interface' is that they cannot be used as Jinja variable
        # context is first serialize as a JSON string with jsonpickle (which nicely handles complex objects serialization)
        # then it is reloaded as a dict. After reload, objects like 'HA' or 'Interface' are no longer objects since they
        # were changed to regular key:value pairs by jsonpickle during the serialization process.
        # One must use json.loads and not jsonpickle.decode to reload the JSON string into a dict otherwise jsonpickle
        # cleverly rebuilds the original 'HA'/'Interface' objects !
        # We need to pass a context dict to Jinja (in order to loop through the items), that's why the serialized context
        # must be deserialized

        import jsonpickle, json
        fortigates = dict()
        for device in status_fortigates:
            fortigates[device['name']] = json.loads(jsonpickle.encode(device['context']))
            for k in ['fmg_ip', 'fos_version', 'HA', 'mgmt_fpoc']:  # list of context keys which are not needed for FMG
                del fortigates[device['name']][k]

        # Render the Jinja dict to be imported in FortiManager
        fortimanager = loader.render_to_string(f'{APPNAME}/fortimanager_provisioning.html',
                                               {'fortigates': fortigates}, using='jinja2')

    # Render the deployment status using Django template engine
    return render(request, f'{APPNAME}/deployment_status.html',
                  {'devices': status_devices, 'fortimanager': fortimanager})
