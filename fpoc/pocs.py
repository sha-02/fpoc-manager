from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render

from fpoc.deploy import start_poc
from fpoc.devices import FortiGate, LXC, Vyos
from fpoc.fortipoc import FortiPoCFoundation1
from collections import namedtuple

APPNAME = "fpoc"


Status = namedtuple('Status', 'is_valid is_invalid message')


def bootstrap(request: WSGIRequest, poc_id: int):
    # This PoC is based on FortiPoC "Foundation1"
    devices = {
        'FGT-A': FortiGate(), 'FGT-A_sec': FortiGate(),
        'FGT-B': FortiGate(), 'FGT-B_sec': FortiGate(),
        'FGT-C': FortiGate(), 'FGT-C_sec': FortiGate(),
        'FGT-D': FortiGate(), 'FGT-D_sec': FortiGate(),
        'ISFW-A': FortiGate(),
    }

    for devname, dev in devices.items():
        dev.name = devname
        dev.template_group = 'bootstrap_configs'
        dev.template_filename = request.POST.get('targetedFOSversion') + '.conf'  # e.g. '6.4.6.conf'
        dev.template_context = {'i': FortiPoCFoundation1.devices[devname].mgmt_lastbyte} # for Django template to
        # render the OOB MGMT IP of this FGT

    device_dependencies = {
        'FGT-A': (), 'FGT-A_sec': (),
        'FGT-B': (), 'FGT-B_sec': (),
        'FGT-C': (), 'FGT-C_sec': (),
        'FGT-D': (), 'FGT-D_sec': (),
        'ISFW-A': (),
    }

    # This PoC is based on FortiPoC "Foundation1"
    if inspect(request).is_invalid:
        return render(request, f'{APPNAME}/error.html', {'error_message': inspect(request).message})
    if request.POST.get('targetedFOSversion') == '':
        return render(request, f'{APPNAME}/error.html', {'error_message': 'The FortiOS version must be specified'})
    status_devices = start_poc(request, FortiPoCFoundation1(request=request, poc_id=poc_id, devices=devices), device_dependencies)
    return render(request, f'{APPNAME}/deployment_status.html', {'devices': status_devices})


def sdwan_simple(request: WSGIRequest, poc_id: int):
    # This PoC is based on FortiPoC "Foundation1"
    context = {
        # Hub is FGT-C from FortiPoC "Fundation1"
        'hub': FortiPoCFoundation1.devices['FGT-C'].wan.inet1.subnet + '.1',  # 100.64.31.1
    }

    devices = {
        'FGT-A': FortiGate(name='FGT-A', template_group='FGT-i', template_context={'i': 1, **context}),
        'FGT-B': FortiGate(name='FGT-B', template_group='FGT-i', template_context={'i': 2, **context}),
        'FGT-C': FortiGate(name='FGT-DC'),

        'PC_A1': LXC(name='PC-A1', template_context={'ipmask': '192.168.1.1/24', 'gateway': '192.168.1.254'}),
        'PC_A2': LXC(name='PC-A2', template_context={'ipmask': '192.168.1.2/24', 'gateway': '192.168.1.254'}),
        'PC_B1': LXC(name='PC-B1', template_context={'ipmask': '192.168.2.1/24', 'gateway': '192.168.2.254'}),
        'PC_B2': LXC(name='PC-B2', template_context={'ipmask': '192.168.2.2/24', 'gateway': '192.168.2.254'}),
        'PC_C1': LXC(name='DC-Server',
                     template_context={'ipmask': '192.168.255.100/24', 'gateway': '192.168.255.254'}),
    }

    device_dependencies = {
        'FGT-A': ('PC_A1', 'PC_A2'),
        'FGT-B': ('PC_B1', 'PC_B2'),
        'FGT-C': ('PC_C1',)
    }

    # This PoC is based on FortiPoC "Foundation1"
    if inspect(request).is_invalid:
        return render(request, f'{APPNAME}/error.html', {'error_message': inspect(request).message})
    status_devices = start_poc(request, FortiPoCFoundation1(request=request, poc_id=poc_id, devices=devices), device_dependencies)
    return render(request, f'{APPNAME}/deployment_status.html', {'devices': status_devices})


def vpn_site2site(request: WSGIRequest, poc_id: int):
    # This PoC is based on FortiPoC "Foundation1"
    context = {
        'vpn': request.POST.get('vpn'),  # 'ipsec', 'gre', ...
        'ike': request.POST.get('ike'),  # 1 or 2
        'routing': request.POST.get('routing'),  # 'static', 'ospf', 'ibgp', ...

        'fgta_inet1': FortiPoCFoundation1.devices['FGT-A'].wan.inet1.subnet + '.1',  # 100.64.11.1
        'fgta_inet2': FortiPoCFoundation1.devices['FGT-A'].wan.inet2.subnet + '.1',  # 100.64.11.1
        'fgtb_inet1': FortiPoCFoundation1.devices['FGT-B'].wan.inet1.subnet + '.2',  # 100.64.21.2
        'fgtb_inet2': FortiPoCFoundation1.devices['FGT-B'].wan.inet2.subnet + '.2',  # 100.64.22.2
    }

    # List of all devices for this Scenario
    devices = {
        'FGT-A': FortiGate(name='FGT-A', template_group='FGT-i', template_context={'i': 1, **context}),
        'FGT-B': FortiGate(name='FGT-B', template_group='FGT-i', template_context={'i': 2, **context}),
        'PC_A1': LXC(name='PC-A1', template_context={'ipmask': '192.168.1.1/24', 'gateway': '192.168.1.254'}),
        'PC_A2': LXC(name='PC-A11', template_context={'ipmask': '192.168.11.1/24', 'gateway': '192.168.11.254'}),
        'PC_B1': LXC(name='PC-B2', template_context={'ipmask': '192.168.2.1/24', 'gateway': '192.168.2.254'}),
        'PC_B2': LXC(name='PC-B22', template_context={'ipmask': '192.168.22.1/24', 'gateway': '192.168.22.254'}),
    }

    device_dependencies = {
        'FGT-A': ('PC_A1', 'PC_A2'),
        'FGT-B': ('PC_B1', 'PC_B2'),
    }

    # This PoC is based on FortiPoC "Foundation1"
    if inspect(request).is_invalid:
        return render(request, f'{APPNAME}/error.html', {'error_message': inspect(request).message})
    status_devices = start_poc(request, FortiPoCFoundation1(request=request, poc_id=poc_id, devices=devices), device_dependencies)
    return render(request, f'{APPNAME}/deployment_status.html', {'devices': status_devices})


def vpn_dialup(request: WSGIRequest, poc_id: int):
    # This PoC is based on FortiPoC "Foundation1"
    context = {
        'ike': request.POST.get('ike'),  # 1 or 2
        'overlay': request.POST.get('overlay'),  # 'static' or 'mode-cfg'
        'routing': request.POST.get('routing'),  # 'ike-routing', 'modecfg-routing', 'ospf', 'ibgp', 'ebgp',
        # 'ibgp-confederation'
        'advpn': bool(request.POST.get('advpn', False)),  # True or False
        'nat_hub': request.POST.get('Hub_NAT'),  # Type of NAT for Hub = 'None', 'DNAT'

        # Hub is FGT-A from FortiPoC "Fundation1"
        'hub': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.1',  # IP when not DNATed: 198.51.100.1
        'hub_dnat': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.201',  # IP when DNATed: 198.51.100.201
    }

    # Some options are exclusive
    if context['routing'] == 'ike-routing' or context['routing'] == 'modecfg-routing':
        context['overlay'] = None
        context['advpn'] = False

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

    device_dependencies = {
        'FGT-A': ('PC_A1',),
        'FGT-B': ('PC_B1',),
        'FGT-C': ('PC_C1',),
        'FGT-D': ('PC_D1',),
    }

    # This PoC is based on FortiPoC "Foundation1"
    if inspect(request).is_invalid:
        return render(request, f'{APPNAME}/error.html', {'error_message': inspect(request).message})
    status_devices = start_poc(request, FortiPoCFoundation1(request=request, poc_id=poc_id, devices=devices), device_dependencies)
    return render(request, f'{APPNAME}/deployment_status.html', {'devices': status_devices})


def vpn_dualhub_singletunnel(request: WSGIRequest, poc_id: int):
    # This PoC is based on FortiPoC "Foundation1"
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

    device_dependencies = {
        'FGT-A': ('PC_A1', 'PC_A2'),
        'FGT-A_sec': ('PC_A1', 'PC_A2'),
        'ISFW-A': (),
        'FGT-B': ('PC_B1',),
        'FGT-C': ('PC_C1',)
    }

    # This PoC is based on FortiPoC "Foundation1"
    if inspect(request).is_invalid:
        return render(request, f'{APPNAME}/error.html', {'error_message': inspect(request).message})
    status_devices = start_poc(request, FortiPoCFoundation1(request=request, poc_id=poc_id, devices=devices), device_dependencies)
    return render(request, f'{APPNAME}/deployment_status.html', {'devices': status_devices})


def sdwan_advpn_workshop(request: WSGIRequest, poc_id: int):
    # This PoC is based on FortiPoC "Foundation1"
    context = {
        'overlay': request.POST.get('overlay'),  # 'static' or 'mode-cfg'
        'duplicate_paths': request.POST.get('duplicate_paths'),
        # 'keep_duplicates', 'onnet_pref_spokes', 'offnet_filter_hub'
        'override_with_hub_nexthop': bool(request.POST.get('override_with_hub_nexthop', False)),  # True or False
        'feasible_routes': request.POST.get('feasible_routes'),  # 'none', 'rfc1918', 'default_route'
        'remote_internet_mpls': bool(request.POST.get('remote_internet_mpls', False)),  # True or False

        # Hub is FGT-A from FortiPoC "Fundation1"
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

    if context['feasible_routes'] == 'default_route':
        # feasible default-route already covers 'remote_internet_mpls'
        context['remote_internet_mpls'] = False

    devices = {
        'FGT-A': FortiGate(name='FGT-DC-3', template_group='FGT-DC', template_context={**context}),
        'FGT-B': FortiGate(name='FGT-SDW-1', template_group='FGT-SDW', template_context={'i': 1, **context}),
        'FGT-C': FortiGate(name='FGT-SDW-2', template_group='FGT-SDW', template_context={'i': 2, **context}),

        'PC_A1': LXC(name='DC-server-4', template_context={'ipmask': '192.168.3.4/24', 'gateway': '192.168.3.3'}),
        'PC_B1': LXC(name='Client-11', template_context={'ipmask': '192.168.1.11/24', 'gateway': '192.168.1.1'}),
        'PC_C1': LXC(name='Client-22', template_context={'ipmask': '192.168.2.22/24', 'gateway': '192.168.2.2'}),
    }

    device_dependencies = {
        'FGT-A': ('PC_A1',),
        'FGT-B': ('PC_B1',),
        'FGT-C': ('PC_C1',)
    }

    # This PoC is based on FortiPoC "Foundation1"
    if inspect(request).is_invalid:
        return render(request, f'{APPNAME}/error.html', {'error_message': inspect(request).message})
    status_devices = start_poc(request, FortiPoCFoundation1(request=request, poc_id=poc_id, devices=devices), device_dependencies)
    return render(request, f'{APPNAME}/deployment_status.html', {'devices': status_devices})


def inspect(request: WSGIRequest) -> Status:
    if request.POST.get('targetedFOSversion'):
        # Ensure the FOS version is of the form: <major>.<minor>.<patch>
        import re
        if not re.match('^\d{1,2}.\d{1,2}.\d{1,2}$', request.POST.get('targetedFOSversion')):
            return Status(False, True, f"This is not a valid FortiOS version: {request.POST.get('targetedFOSversion')}")

    if request.POST.get('fpocIP'):
        # Ensure a valid IP address is provided
        import ipaddress
        try:
            ipaddress.ip_address(request.POST.get('fpocIP'))  # throws an exception if the IP address is not valid
        except:
            return Status(False, True, f"This is not a valid IP address: {request.POST.get('fpocIP')}")

    if request.POST.get('previewOnly') and not request.POST.get('targetedFOSversion'):
        return Status(False, True, 'FOS version must be specified when preview-only is selected')

    return Status(True, False, 'request is valid')
