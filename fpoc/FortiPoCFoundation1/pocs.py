import threading

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse

from collections import namedtuple
import copy

import fpoc
import fpoc.fortios as fortios
from fpoc import FortiGate, FortiGate_HA, LXC, FortiManager, VyOS
from fpoc.FortiPoCFoundation1 import FortiPoCFoundation1
import fpoc.ansible as ansible

import ipaddress

APPNAME = "fpoc/FortiPoCFoundation1"

Status = namedtuple('Status', 'is_valid is_invalid message')


def FOS(fos_version_target: str):  # converts a FOS version string "6.0.13" to a long integer 6_000_013
    major, minor, patch = fos_version_target.split('.')
    return int(major) * 1_000_000 + int(minor) * 1_000 + int(patch)


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
    fundation1_devices.update(FortiPoCFoundation1.devices_of_type(VyOS))  # + all VyOS devices

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
    if not request.POST.get('targetedFOSversion'):
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


def l2vpn(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    context = {
        'l2vpn': request.POST.get('l2vpn'),  # 'vxlan-ipsec', 'vxlan'
        'ipsec': True if 'ipsec' in request.POST.get('l2vpn') else False,
        'control_plane': request.POST.get('control_plane'),  # 'mp-bgp', 'flood-and-learn'

        # Used as VTEPs or as IPsec termination
        'sites': {
            1:  {
                'ip': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.1',  # 198.51.100.1
                'gw': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.254',  # 198.51.100.254
            },
            2:  {
                'ip': FortiPoCFoundation1.devices['FGT-B'].wan.inet.subnet + '.2',  # 203.0.113.2
                'gw': FortiPoCFoundation1.devices['FGT-B'].wan.inet.subnet + '.254',  # 203.0.113.254
            },
            3:  {
                'ip': FortiPoCFoundation1.devices['FGT-C'].wan.inet.subnet + '.3',  # 192.0.2.3
                'gw': FortiPoCFoundation1.devices['FGT-C'].wan.inet.subnet + '.254',  # 192.0.2.254
            },
        }
    }

    messages = []    # list of messages displayed along with the rendered configurations
    errors = []     # List of errors

    targetedFOSversion = FOS(request.POST.get('targetedFOSversion') or '0.0.0') # use '0.0.0' if empty targetedFOSversion string, FOS version becomes 0
    minimumFOSversion = 0

    if context['control_plane'] == 'mp-bgp':
        minimumFOSversion = max(minimumFOSversion, 7_004_000)

    if context['control_plane'] == 'flood-and-learn':
        poc_id = None ; errors.append("flood-and-learn not yet done")

    if poc_id is None:
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': errors})

    if targetedFOSversion and minimumFOSversion > targetedFOSversion:
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': f'The minimum version for the selected options is {minimumFOSversion:_}'})

    messages.insert(0, f"Minimum FortiOS version required for the selected set of features: {minimumFOSversion:_}")

    # List of all devices for all Scenario
    lxcs = {
        'PC-A11': {'ipmask': '192.168.10.1/24', 'vlan': 10},
        'PC-A21': {'ipmask': '192.168.20.1/24', 'vlan': 20},
        'PC-B12': {'ipmask': '192.168.10.2/24', 'vlan': 10},
        'PC-B22': {'ipmask': '192.168.20.2/24', 'vlan': 20},
        'PC-C13': {'ipmask': '192.168.10.3/24', 'vlan': 10},
        'PC-C23': {'ipmask': '192.168.20.3/24', 'vlan': 20},
    }

    context = {
        'lxcs': lxcs,
        'vlans': [10, 20],
        'vnis': [100, 200],
        **context
    }

    devices = {
        'FGT-A': FortiGate(name='FGT-A', template_group='SITES', template_context={'id': 1, **context}),
        'FGT-B': FortiGate(name='FGT-B', template_group='SITES', template_context={'id': 2, **context}),
        'FGT-C': FortiGate(name='FGT-C', template_group='SITES', template_context={'id': 3, **context}),
        'Internet': VyOS(template_context={'sites': context['sites']}),

        'PC_A1': LXC(name='PC-A11', template_context=lxcs['PC-A11']),
        'PC_A2': LXC(name='PC-A21', template_context=lxcs['PC-A21']),
        'PC_B1': LXC(name='PC-B12', template_context=lxcs['PC-B12']),
        'PC_B2': LXC(name='PC-B22', template_context=lxcs['PC-B22']),
        'PC_C1': LXC(name='PC-C13', template_context=lxcs['PC-C13']),
        'PC_C2': LXC(name='PC-C23', template_context=lxcs['PC-C23']),
    }

    if context['ipsec']:    # Only FGT-A and FGT-B are used, FGT-C is not part of this scenario
        del(devices['FGT-C']); del(devices['PC_C1']); del(lxcs['PC-C13']); del(devices['PC_C2']); del(lxcs['PC-C23'])
        del(devices['Internet'])

    # Monkey patching used to pass some parameters inside the existing request object
    request.fpoc = dict()
    request.fpoc['poc_id'] = poc_id
    request.fpoc['FOS_minimum'] = minimumFOSversion
    request.fpoc['messages'] = messages

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


def sdwan_advpn_dualdc(request: WSGIRequest) -> HttpResponse:
    """
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

    def lan_segment(segments: dict):
        return {'name': 'port5', **segments['port5']}

    def vrf_segments(segments: dict, context: dict):
        if not context['vrf_aware_overlay']:
            return {}

        return segments

    def lxc_context(lxc_name: str, segments_devices: dict, context: dict):
        segments = segments_devices[lxc_name]

        base_segment = {'ipmask': segments['port5']['ip_lxc'] + '/' + segments['port5']['mask'],
                        'gateway': segments['port5']['ip']}

        # Construct the list of all LXCs with their IPs to populate the /etc/hosts of each LXC
        hosts = []
        for name, segs in segments_devices.items():
            if not context['vrf_aware_overlay']:
                new_name = f"PC-{name}".replace("_", "-").replace("LAN-", "")
                hosts.append({'name': new_name, 'ip': lan_segment(segs)['ip_lxc']})
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
        'vrf_wan': int(request.POST.get('vrf_wan')),  # [0-251] VRF for Internet and MPLS links
        'vrf_pe': int(request.POST.get('vrf_pe')),  # [0-251] VRF for IPsec tunnels
        'vrf_seg0': int(request.POST.get('vrf_seg0')),  # [0-251] port5 (no vlan) segment
        'vrf_seg1': int(request.POST.get('vrf_seg1')),  # [0-251] vlan segment
        'vrf_seg2': int(request.POST.get('vrf_seg2')),  # [0-251] vlan segment
        'multicast': bool(request.POST.get('multicast', False)),  # True or False
        'shortcut_routing': request.POST.get('shortcut_routing'),  # 'exchange_ip', 'ipsec_selectors', 'dynamic_bgp'
        'bgp_design': request.POST.get('bgp_design'),  # 'per_overlay', 'per_overlay_legacy', 'on_loopback', 'no_bgp'
        'overlay': request.POST.get('overlay'),  # 'static' or 'mode_cfg'
    }

    # Define the poc_id based on the options which were selected

    poc_id = None
    messages = []    # list of messages displayed along with the rendered configurations
    errors = []     # List of errors

    targetedFOSversion = FOS(request.POST.get('targetedFOSversion') or '0.0.0') # use '0.0.0' if empty targetedFOSversion string, FOS version becomes 0
    minimumFOSversion = 0

    if context['bidir_sdwan'] in ('none', 'route_tag'):  # 'or'
        context['bgp_priority'] = None

    if context['bgp_design'] == 'per_overlay_legacy':  # BGP per overlay, legacy 6.4+ style
        poc_id = 6
        minimumFOSversion = max(minimumFOSversion, 6_004_000)

    if context['bgp_design'] == 'per_overlay':  # BGP per overlay, 7.0+ style
        poc_id = 9
        minimumFOSversion = max(minimumFOSversion, 7_000_000)

        if context['vrf_aware_overlay']:
            minimumFOSversion = max(minimumFOSversion, 7_002_000)
            poc_id = None  # TODO
            errors.append("vrf_aware_overlay not yet available with BGP per overlay")

        if context['shortcut_routing'] == 'dynamic_bgp':
            minimumFOSversion = max(minimumFOSversion, 7_004_001)
            poc_id = None  # TODO
            errors.append("Dynamic BGP over shortcuts not yet available with BGP per overlay")

        if context['bidir_sdwan'] == 'remote_sla':
            context['overlay'] = 'static'   # remote-sla with bgp-per-overlay can only work with static-overlay IP@
            messages.append("Bidirectional SD-WAN with remote_sla was requested: overlay was forced to 'static'")

        if context['full_mesh_ipsec']:
            context['full_mesh_ipsec'] = False   # Full-mesh IPsec not implemented for bgp-per-overlay
            messages.append("Full-mesh IPsec not implemented for bgp-per-overlay: option is forced to 'False'")


    if context['bgp_design'] == 'on_loopback':  # BGP on loopback, as of 7.0.4
        poc_id = 10
        minimumFOSversion = max(minimumFOSversion, 7_000_004)

        if not context['multicast']:
            context['overlay'] = None   # Unnumbered IPsec tunnels are used if there is no need for multicast routing
            messages.append("Multicast is not requested: unnumbered IPsec tunnels are used")
        else:
            messages.append(f"Multicast is requested: <b>IPsec tunnels are numbered</b> with '{context['overlay']}' overlay")
            if context['vrf_aware_overlay']:
                messages.append(f"for multicast to work <b>vrf_wan, vrf_pe and vrf_seg0 have ALL been forced to VRF 0</b>")
                context['vrf_wan'] = context['vrf_pe'] = context['vrf_seg0'] = 0

        if context['bidir_sdwan'] in ('route_tag', 'route_priority'):  # 'or'
            context['bidir_sdwan'] = 'remote_sla'  # route_tag and route_priority only works with BGP per overlay
            messages.append("Bi-directional SD-WAN was requested: method was forced to 'remote-sla' which is the only "
                           "supported method with bgp-on-loopback")

        if context['bidir_sdwan'] == 'remote_sla':
            minimumFOSversion = max(minimumFOSversion, 7_002_001)

        if context['shortcut_routing'] == 'dynamic_bgp':
            minimumFOSversion = max(minimumFOSversion, 7_004_001)
            poc_id = None  # TODO
            errors.append("Dynamic BGP over shortcuts not yet available with BGP on loopback")

        if context['vrf_aware_overlay']:
            minimumFOSversion = max(minimumFOSversion, 7_002_000)
            for vrf_name in ('vrf_wan', 'vrf_pe', 'vrf_seg0', 'vrf_seg1', 'vrf_seg2'):
                if context[vrf_name] > 251 or context[vrf_name] < 0:
                    poc_id = None; errors.append('VRF id must be within [0-251]')
            if context['vrf_pe'] in (context['vrf_seg1'], context['vrf_seg2']):
                poc_id = None; errors.append("Only port5/seg0/BLUE VRF can be in the same VRF as the PE VRF")
            ce_vrfids = [context['vrf_seg0'], context['vrf_seg1'], context['vrf_seg2']] # list of all CE VRF IDs
            if len(set(ce_vrfids)) != len(ce_vrfids):  # check if the CE VRF IDs are all unique
                poc_id = None; errors.append('All CE VRF IDs must be unique')
            if context['vrf_wan'] != context['vrf_pe']:
                messages.append("<b>ATTENTION:</b> Remote Internet Breakout cannot work with PE-VRF <> WAN-VRF "
                                "because the Internet interfaces are in WAN-VRF and the MPLS overlays are in PE-VRF "
                                "it is therefore not possible to perform traffic steering between UL_INET and OL_MPLS")
            if context['cross_region_advpn']:
                messages.append("Cross-Regional ADVPN was requested but <b>this does not work</b> with VPNv4 eBGP next-hop-unchanged (tested with FOS 7.2.5)"
                                "<br>The BGP NH of VPNv4 prefixes is always set to the BGP loopback of the DC when advertised to eBGP peer"
                                "<br>It breaks all cross-regional shortcut routing convergence: inter-region branch-to-branch and inter-region branch-to-DC")

            messages.append("BGP Route-reflection (for ADVPN) is done only for VRFs BLUE and YELLOW. No RR (no ADPVPN) for VRF RED")
            messages.append("CE VRFs of WEST-BR1/BR2 have DIA while there is no DIA for the CE VRFs of EAST-BR1 (only RIA)")


    if context['bgp_design'] == 'per_overlay' and context['shortcut_routing'] == 'ipsec_selectors':
        # ADVPN shortcuts negotiated with phase2 selectors (no BGP RR)
        poc_id = 7
        minimumFOSversion = max(minimumFOSversion, 7_002_000)

        if context['vrf_aware_overlay']:
            context['vrf_aware_overlay'] = False  # shortcuts from ph2 selectors are incompatible with vpn-id-ipip
            messages.append("VRF-aware overlay was requested but is disabled since it is not supported with shortcuts from phase2 selectors")

        if context['bidir_sdwan'] == 'none':  # Hub-side steering is required because shortcuts do not hide the parent
            context['bidir_sdwan'] = 'route_priority'  # do not default to 'remote_sla' since it is broken with shortcuts based off IPsec selectors
            messages.append("Bidirectional SDWAN was not requested. It is however enabled (with BGP priority) "
                           "because it is needed: shortcuts do not hide the parent with ADVPN from IPsec selectors")

        if context['bidir_sdwan'] == 'remote_sla':
            minimumFOSversion = max(minimumFOSversion, 7_002_001)
            context['overlay'] = 'static'   # remote-sla with bgp-per-overlay can only work with static-overlay IP@
            messages.append("Bidirectional SDWAN with 'remote-sla' was requested: overlay is forced to 'static' since "
                           "remote-sla with bgp-per-overlay can only work with static-overlay IP@")


    if context['bgp_design'] == 'on_loopback' and context['shortcut_routing'] == 'ipsec_selectors':
        minimumFOSversion = max(minimumFOSversion, 7_002_000)
        poc_id = None   # TODO
        errors.append("ADVPN from IPsec selectors not yet available with BGP on loopback")

    if context['bgp_design'] == 'no_bgp':  # No BGP, as of 7.2
        minimumFOSversion = max(minimumFOSversion, 7_002_000)
        poc_id = None   # TODO
        errors.append("SD-WAN+ADVPN design without BGP is not yet available")

    if poc_id is None:
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': errors})

    if targetedFOSversion and minimumFOSversion > targetedFOSversion:
        return render(request, f'{APPNAME}/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': f'The minimum version for the selected options is {minimumFOSversion:_}'})

    messages.insert(0, f"Minimum FortiOS version required for the selected set of features: {minimumFOSversion:_}")

    #
    # LAN underlays / segments
    #

    vrf = {
        'port5': { 'vrfid': context['vrf_seg0'], 'vlanid': 0, 'alias': 'LAN_BLUE' },
        'SEGMENT_1': { 'vrfid': context['vrf_seg1'], 'vlanid': 1001, 'alias': 'LAN_YELLOW' },
        'SEGMENT_2': { 'vrfid': context['vrf_seg2'], 'vlanid': 1002, 'alias': 'LAN_RED' },
    }

    segments_devices = {
        'WEST-DC1': {
            'port5': {'ip': '10.1.0.1/24', 'ip_lxc': '10.1.0.7', **vrf['port5']},
            'SEGMENT_1': {'ip': '10.1.1.1/24', 'ip_lxc': '10.1.1.7', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.1.2.1/24', 'ip_lxc': '10.1.2.7', **vrf['SEGMENT_2']},
        },
        'WEST-DC2': {
            'port5': {'ip': '10.2.0.1/24', 'ip_lxc': '10.2.0.7', **vrf['port5']},
            'SEGMENT_1': {'ip': '10.2.1.1/24', 'ip_lxc': '10.2.1.7', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.2.2.1/24', 'ip_lxc': '10.2.2.7', **vrf['SEGMENT_2']},
        },
        'WEST-BR1': {
            'port5': {'ip': '10.0.1.1/24', 'ip_lxc': '10.0.1.101', **vrf['port5']},
            'SEGMENT_1': {'ip': '10.0.11.1/24', 'ip_lxc': '10.0.11.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.0.21.1/24', 'ip_lxc': '10.0.21.101', **vrf['SEGMENT_2']},
        },
        'WEST-BR2': {
            'port5': {'ip': '10.0.2.1/24', 'ip_lxc': '10.0.2.101', **vrf['port5']},
            'SEGMENT_1': {'ip': '10.0.12.1/24', 'ip_lxc': '10.0.12.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.0.22.1/24', 'ip_lxc': '10.0.22.101', **vrf['SEGMENT_2']},
        },
        'EAST-DC1': {
            'port5': {'ip': '10.4.0.1/24', 'ip_lxc': '10.4.0.7', **vrf['port5']},
            'SEGMENT_1': {'ip': '10.4.10.1/24', 'ip_lxc': '10.4.10.7', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.4.20.1/24', 'ip_lxc': '10.4.20.7', **vrf['SEGMENT_2']},
        },
        'EAST-BR1': {
            'port5': {'ip': '10.4.1.1/24', 'ip_lxc': '10.4.1.101', **vrf['port5']},
            'SEGMENT_1': {'ip': '10.4.11.1/24', 'ip_lxc': '10.4.11.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.4.21.1/24', 'ip_lxc': '10.4.21.101', **vrf['SEGMENT_2']},
        },
        'EAST-DC3': {
            'port5': {'ip': '10.3.0.1/24', 'ip_lxc': '10.3.0.7', **vrf['port5']},
            'SEGMENT_1': {'ip': '10.3.1.1/24', 'ip_lxc': '10.3.1.7', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.3.2.1/24', 'ip_lxc': '10.3.2.7', **vrf['SEGMENT_2']},
        },
        'EAST-BR3': {
            'port5': {'ip': '10.0.3.1/24', 'ip_lxc': '10.0.3.101', **vrf['port5']},
            'SEGMENT_1': {'ip': '10.0.13.1/24', 'ip_lxc': '10.0.13.101', **vrf['SEGMENT_1']},
            'SEGMENT_2': {'ip': '10.0.23.1/24', 'ip_lxc': '10.0.23.101', **vrf['SEGMENT_2']},
        }
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
        'WEST-DC1': '10.200.1.254',
        'WEST-DC2': '10.200.1.253',
        'EAST-DC1': '10.200.2.254',
        'EAST-DC2': '10.200.2.253',
    }

    # Name and id of EAST devices is different between poc10 and other pocs (poc9, poc7)
    if poc_id == 10:  # PoC with BGP on loopback design: Regional LAN summaries are possible
        east_dc_ = {'name': 'EAST-DC1', 'dc_id': 1, 'lxc': 'PC-EAST-DC1'}
        east_br_ = {'name': 'EAST-BR1', 'branch_id': 1, 'lxc': 'PC-EAST-BR1'}
    else:  # Other PoCs with BGP per overlay design: No Regional LAN summaries (IP plan would overlap between Region)
        east_dc_ = {'name': 'EAST-DC3', 'dc_id': 3, 'lxc': 'PC-EAST-DC3'}
        east_br_ = {'name': 'EAST-BR3', 'branch_id': 3, 'lxc': 'PC-EAST-BR3'}

    west_dc1_ = {
                    'id': 1,
                    'inet1': FortiPoCFoundation1.devices['FGT-A'].wan.inet1.subnet + '.1',  # 100.64.11.1
                    'inet2': FortiPoCFoundation1.devices['FGT-A'].wan.inet2.subnet + '.1',  # 100.64.12.1
                    'mpls': FortiPoCFoundation1.devices['FGT-A'].wan.mpls1.subnet + '.1',  # 10.0.14.1
                    'lan': lan_segment(segments_devices['WEST-DC1'])['ip'],
                    'loopback': dc_loopbacks['WEST-DC1'] if poc_id==10 else None
                }

    west_dc2_ = {
                    'id': 2,
                    'inet1': FortiPoCFoundation1.devices['FGT-B'].wan.inet1.subnet + '.2',  # 100.64.21.2
                    'inet2': FortiPoCFoundation1.devices['FGT-B'].wan.inet2.subnet + '.2',  # 100.64.22.2
                    'mpls': FortiPoCFoundation1.devices['FGT-B'].wan.mpls1.subnet + '.2',  # 10.0.24.2
                    'lan': lan_segment(segments_devices['WEST-DC2'])['ip'],
                    'loopback': dc_loopbacks['WEST-DC2'] if poc_id==10 else None
                }

    east_dc1_ = {
                    'id': 3,
                    'inet1': FortiPoCFoundation1.devices['FGT-B_sec'].wan.inet1.subnet + '.3',  # 100.64.121.3
                    'inet2': FortiPoCFoundation1.devices['FGT-B_sec'].wan.inet2.subnet + '.3',  # 100.64.122.3
                    'mpls': FortiPoCFoundation1.devices['FGT-B_sec'].wan.mpls1.subnet + '.3',  # 10.0.124.3
                    'lan': lan_segment(segments_devices[east_dc_['name']])['ip'],
                    'loopback': dc_loopbacks['EAST-DC1'] if poc_id==10 else None
                }

    east_dc2_ = {  # Fictitious second DC for East region
                    'id': 4,
                    'inet1': FortiPoCFoundation1.devices['FGT-B_sec'].wan.inet1.subnet + '.4',  # 100.64.121.4
                    'inet2': FortiPoCFoundation1.devices['FGT-B_sec'].wan.inet2.subnet + '.4',  # 100.64.122.4
                    'mpls': FortiPoCFoundation1.devices['FGT-B_sec'].wan.mpls1.subnet + '.4',  # 10.0.124.4
                    'lan': '0.0.0.0',
                    'loopback': dc_loopbacks['EAST-DC2'] if poc_id==10 else None
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

    # 'direct_internet_access' is only for the CE VRF of the Branches. Hubs must have DIA for its CE VRFs, it's not optional.
    # 'inter_segments' describe the inter-vrf links used for DIA.

    west_dc1 = FortiGate(name='WEST-DC1', template_group='DATACENTERS',
                         template_context={'region': 'West', 'region_id': 1, 'dc_id': 1,
                                           'loopback': dc_loopbacks['WEST-DC1'] if poc_id==10 else None,
                                           'lan': lan_segment(segments_devices['WEST-DC1']),
                                           'vrf_segments': vrf_segments(segments_devices['WEST-DC1'],context),
                                           'inter_segments': inter_segments,
                                           'datacenter': datacenters,
                                           **context})
    west_dc2 = FortiGate(name='WEST-DC2', template_group='DATACENTERS',
                         template_context={'region': 'West', 'region_id': 1, 'dc_id': 2,
                                           'loopback': dc_loopbacks['WEST-DC2'] if poc_id==10 else None,
                                           'lan': lan_segment(segments_devices['WEST-DC2']),
                                           'vrf_segments': vrf_segments(segments_devices['WEST-DC2'],context),
                                           'inter_segments': inter_segments,
                                           'datacenter': datacenters,
                                           **context})
    west_br1 = FortiGate(name='WEST-BR1', template_group='BRANCHES',
                         template_context={'region': 'West', 'region_id': 1, 'branch_id': 1,
                                           'loopback': '10.200.1.1' if poc_id==10 else None,
                                           'lan': lan_segment(segments_devices['WEST-BR1']),
                                           'vrf_segments': vrf_segments(segments_devices['WEST-BR1'],context),
                                           'direct_internet_access': True, 'inter_segments': inter_segments,
                                           'datacenter': datacenters['west'],
                                           **context})
    west_br2 = FortiGate(name='WEST-BR2', template_group='BRANCHES',
                         template_context={'region': 'West', 'region_id': 1, 'branch_id': 2,
                                           'loopback': '10.200.1.2' if poc_id==10 else None,
                                           'lan': lan_segment(segments_devices['WEST-BR2']),
                                           'vrf_segments': vrf_segments(segments_devices['WEST-BR2'],context),
                                           'direct_internet_access': True, 'inter_segments': inter_segments,
                                           'datacenter': datacenters['west'],
                                           **context})
    east_dc = FortiGate(name=east_dc_['name'], template_group='DATACENTERS',
                        template_context={'region': 'East', 'region_id': 2, 'dc_id': east_dc_['dc_id'],
                                          'loopback': dc_loopbacks['EAST-DC1'] if poc_id == 10 else None,
                                          'lan': lan_segment(segments_devices[east_dc_['name']]),
                                          'vrf_segments': vrf_segments(segments_devices[east_dc_['name']], context),
                                          'inter_segments': inter_segments,
                                           'datacenter': datacenters,
                                           **context})
    east_br = FortiGate(name=east_br_['name'], template_group='BRANCHES',
                        template_context={'region': 'East', 'region_id': 2, 'branch_id': east_br_['branch_id'],
                                          'loopback': '10.200.2.1' if poc_id == 10 else None,
                                          'lan': lan_segment(segments_devices[east_br_['name']]),
                                          'vrf_segments': vrf_segments(segments_devices[east_br_['name']], context),
                                          'direct_internet_access': False, 'inter_segments': {}, # inter_segments,
                                           'datacenter': datacenters['east'],
                                           **context})

    devices = {
        'FGT-A': west_dc1,
        'FGT-B': west_dc2,
        'FGT-B_sec': east_dc,
        'FGT-C': west_br1,
        'FGT-D': west_br2,
        'FGT-D_sec': east_br,
        'FMG': FortiManager(name='FMG'),

        'PC_A1': LXC(name='PC-WEST-DC1', template_context=lxc_context('WEST-DC1', segments_devices, context)),
        'PC_B1': LXC(name='PC-WEST-DC2', template_context=lxc_context('WEST-DC2', segments_devices, context)),
        'PC_B2': LXC(name=east_dc_['lxc'], template_context=lxc_context(east_dc_['name'], segments_devices, context)),
        'PC_C1': LXC(name='PC-WEST-BR1', template_context=lxc_context('WEST-BR1', segments_devices, context)),
        'PC_D1': LXC(name='PC-WEST-BR2', template_context=lxc_context('WEST-BR2', segments_devices, context)),
        'PC_D2': LXC(name=east_br_['lxc'], template_context=lxc_context(east_br_['name'], segments_devices, context)),
        'SRV_INET': LXC(name='INTERNET-SERVER', template_filename='lxc_SRV_INET.conf')
    }

    # Monkey patching used to pass some parameters inside the existing request object
    request.fpoc = dict()
    request.fpoc['poc_id'] = poc_id
    request.fpoc['FOS_minimum'] = minimumFOSversion
    request.fpoc['messages'] = messages

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
        fortigates = dict()
        for device in status_fortigates:
            device['context']['wan'] = device['context']['wan'].dictify()
            fortigates[device['name']] = copy.deepcopy(device['context'])
            for k in ['fmg_ip', 'fos_version', 'HA', 'mgmt_fpoc']:  # list of context keys which are not needed for FMG
                del fortigates[device['name']][k]

        # ++ Previous approach ++
        # rendered obsolete by using a dictify method for 'Interface' and 'WAN' objects
        # and by not exposing the HA object to FMG
        #
        # Then serialize the contexts in JSON so that they can be used as a Jinja variable
        # Problem with context objects like 'HA' and 'Interface' is that they cannot be used as Jinja variable
        # context is first serialize as a JSON string with jsonpickle (which nicely handles complex objects serialization)
        # then it is reloaded as a dict. After reload, objects like 'HA' or 'Interface' are no longer objects since they
        # were changed to regular key:value pairs by jsonpickle during the serialization process.
        # One must use json.loads and not jsonpickle.decode to reload the JSON string into a dict otherwise jsonpickle
        # cleverly rebuilds the original 'HA'/'Interface' objects !
        # We need to pass a context dict to Jinja (in order to loop through the items), that's why the serialized context
        # must be deserialized

        # import jsonpickle, json
        # fortigates = dict()
        # for device in status_fortigates:
        #     fortigates[device['name']] = json.loads(jsonpickle.encode(device['context']))
        #     for k in ['fmg_ip', 'fos_version', 'HA', 'mgmt_fpoc']:  # list of context keys which are not needed for FMG
        #         del fortigates[device['name']][k]

        # Render the Jinja dict to be imported in FortiManager
        fortimanager = loader.render_to_string(f'{APPNAME}/fortimanager_provisioning.html',
                                               {'fortigates': fortigates}, using='jinja2')

    # Render the deployment status using Django template engine
    messages = request.fpoc['messages'] if hasattr(request, 'fpoc') else ["<no message>"]
    return render(request, f'{APPNAME}/deployment_status.html',
                  {'poc_id': poc_id, 'devices': status_devices, 'fortimanager': fortimanager, 'messages': messages})
