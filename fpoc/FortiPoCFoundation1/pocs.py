from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import fpoc
from fpoc import FortiGate, LXC, VyOS
from fpoc.FortiPoCFoundation1 import FortiPoCFoundation1

# def upgrade(request: WSGIRequest) -> HttpResponse:
#     """
#     """
#
#     fos_version_target = request.POST.get('targetedFOSversion')
#     if not fos_version_target:
#         return render(request, f'fpoc/message.html',
#                       {'title': 'Error', 'header': 'Error', 'message': 'FortiOS version must be provided'})
#
#     # the intersection of the keys of request.POST dict and the foundation1 dict keys produces the keys of each
#     # device to be upgraded
#     fortigates = FortiPoCFoundation1.devices_of_type(FortiGate)  # All FortiGate devices
#     fortigates = sorted(list(request.POST.keys() & fortigates.keys()))
#
#     if request.POST.get('previewOnly'):
#         return render(request, f'fpoc/message.html',
#                       {'title': 'Upgrade', 'header': 'Upgrade preview', 'message': fortigates})
#
#     def _upgrade_fgt(device: FortiGate, fos_version_target: str, lock: threading.Lock):
#         fortios.prepare_api(device)  # create API admin and key if needed
#         fortios.update_fortios_version(device, fos_version_target, lock)  # Upgrade/Downgrade FortiGate
#
#     poc = FortiPoCFoundation1(request, fpoc_devnames=fortigates)
#     threads = list()
#     for fgt in poc:
#         print(f'{fgt.name} : Upgrading to FortiOS', request.POST.get('targetedFOSversion'), ' ...')
#         thread = threading.Thread(target=_upgrade_fgt, args=(fgt, fos_version_target, poc.lock))
#         threads.append(thread)
#         thread.start()
#
#     for index, thread in enumerate(threads):
#         thread.join()
#
#     return render(request, f'fpoc/message.html',
#                   {'title': 'Upgrade', 'header': 'Upgrade status', 'message': fortigates})
#
#
# def poweron(request: WSGIRequest) -> HttpResponse:
#     """
#     """
#     fundation1_devices = FortiPoCFoundation1.devices_of_type(FortiGate)  # All FortiGate devices
#     fundation1_devices.update(FortiPoCFoundation1.devices_of_type(LXC))  # + all LXC devices
#     fundation1_devices.update(FortiPoCFoundation1.devices_of_type(VyOS))  # + all VyOS devices
#
#     # the intersection of the keys of request.POST dict and the fundation1 dict keys produces the keys of each
#     # device to be powered on
#     devices_to_start = sorted(list(request.POST.keys() & fundation1_devices.keys()))
#
#     if request.POST.get('previewOnly'):
#         return render(request, f'fpoc/message.html',
#                       {'title': 'Power-On', 'header': 'Power-On preview', 'message': devices_to_start})
#
#     # Create an FPOC instance because we need to know the IP@ to be used to reach the FPOC
#     poc = FortiPoCFoundation1(request)
#
#     # TODO: admin & pwd should be stored in DB so that it can be customized per FortiPoC (like WAN_CTRL)
#     _, result = ansible.poweron_devices(devices_to_start, host=poc.ip, admin='admin', pwd='')
#     result = '<pre> ' + result + ' </pre>'
#
#     return render(request, f'fpoc/message.html',
#                   {'title': 'Power-On', 'header': 'Power-On status', 'message': result})


# def bootstrap(request: WSGIRequest, poc_id: int) -> HttpResponse:
#     """
#     """
#     # Check the request
#     if not request.POST.get('targetedFOSversion'):
#         return render(request, f'{APPNAME}/message.html',
#                       {'title': 'Error', 'header': 'Error', 'message': 'The FortiOS version must be specified'})
#
#     devices = FortiPoCFoundation1.devices_of_type(FortiGate)  # All FortiGate devices
#
#     for fpoc_devname, device in devices.items():
#         device.template_filename = request.POST.get('targetedFOSversion') + '.conf'  # e.g. '6.4.6.conf'
#
#         device.template_context = {'name': fpoc_devname, 'mgmt': FortiPoCFoundation1.devices[fpoc_devname].mgmt}
#         if bool(request.POST.get('WAN_underlays', False)) and device.wan is not None:
#             device.template_context['WAN_underlays'] = True
#             device.template_context['wan'] = device.wan
#             device.template_context['ip_lastbyte'] = device.offset + 1
#         else:
#             device.template_context['WAN_underlays'] = False
#
#         if request.POST.get('HA') == 'FGCP':
#             device.ha = FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, group_id=1, group_name=fpoc_devname,
#                                      hbdev=[('port6', 0)], sessyncdev=['port6'],
#                                      monitordev=['port1', 'port2', 'port5'], priority=128)
#             if fpoc_devname in ('FGT-A_sec', 'FGT-B_sec', 'FGT-C_sec', 'FGT-D_sec'):
#                 device.ha.role = FortiGate_HA.Roles.SECONDARY
#             else:
#                 device.ha.role = FortiGate_HA.Roles.PRIMARY
#
#     devices['FMG'] = FortiManager(name='FMG')
#
#     # Render and deploy the configs
#     return fpoc.start(request, poc_id, devices, class_=FortiPoCFoundation1)


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
    return fpoc.start(FortiPoCFoundation1(request, poc_id), devices)


def l2vpn(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    """
    context = {
        'l2vpn': request.POST.get('l2vpn'),  # 'vxlan-ipsec', 'vxlan'
        'ipsec': True if 'ipsec' in request.POST.get('l2vpn') else False,
        'ipsec_design': request.POST.get('ipsec_design'),  # 'site2site', 'full-mesh', 'advpn'
        'ipsec_site2site': True if ('ipsec' in request.POST.get('l2vpn') and request.POST.get('ipsec_design') == 'site2site') else False,
        'control_plane': request.POST.get('control_plane'),  # 'mp-bgp', 'flood-and-learn'

        # Used as VTEPs or as IPsec termination
        'sites': {
            1:  {
                'name': 'FGT-A',
                'ip': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.1',  # 198.51.100.1
                'gw': FortiPoCFoundation1.devices['FGT-A'].wan.inet.subnet + '.254',  # 198.51.100.254
            },
            2:  {
                'name': 'FGT-B',
                'ip': FortiPoCFoundation1.devices['FGT-B'].wan.inet.subnet + '.2',  # 203.0.113.2
                'gw': FortiPoCFoundation1.devices['FGT-B'].wan.inet.subnet + '.254',  # 203.0.113.254
            },
            3:  {
                'name': 'FGT-C',
                'ip': FortiPoCFoundation1.devices['FGT-C'].wan.inet.subnet + '.3',  # 192.0.2.3
                'gw': FortiPoCFoundation1.devices['FGT-C'].wan.inet.subnet + '.254',  # 192.0.2.254
            },
            4:  {
                'name': 'FGT-D',
                'ip': FortiPoCFoundation1.devices['FGT-D'].wan.inet.subnet + '.4',  # 100.64.40.4
                'gw': FortiPoCFoundation1.devices['FGT-D'].wan.inet.subnet + '.254',  # 100.64.40.254
            },
        }
    }

    messages = []    # list of messages displayed along with the rendered configurations
    errors = []     # List of errors

    targetedFOSversion = FortiGate.FOS_int(request.POST.get('targetedFOSversion') or '0.0.0') # use '0.0.0' if empty targetedFOSversion string, FOS version becomes 0
    minimumFOSversion = 0

    if context['control_plane'] == 'mp-bgp':
        minimumFOSversion = max(minimumFOSversion, 7_004_000)

        if context['ipsec_design'] == 'advpn':
            messages.append("Hub-and-Spoke design <b>does not work</b> with VxLAN (regardless of ADVPN) (FOS 7.4.1)"
                            "<br>When the Hub receives a VXLAN packet from a Branch, it is not forwarded to the destination Branch"
                            "<br>Debug flow shows receiving the vxlan udp packet and nothing more"
                            "<br>To be tried again with an ADVPN 2.0 design (if shortcut creation is not driven by traffic)")

    if context['control_plane'] == 'flood-and-learn':
        poc_id = None; errors.append("flood-and-learn not yet done")

    if poc_id is None:
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': errors})

    if targetedFOSversion and minimumFOSversion > targetedFOSversion:
        return render(request, f'fpoc/message.html',
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
        'PC-D14': {'ipmask': '192.168.10.4/24', 'vlan': 10},
        'PC-D24': {'ipmask': '192.168.20.4/24', 'vlan': 20},
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
        'FGT-D': FortiGate(name='FGT-D', template_group='SITES', template_context={'id': 4, **context}),
        'Internet': VyOS(template_context={'sites': context['sites'], 'ipsec': context['ipsec']}),

        'PC_A1': LXC(name='PC-A11', template_context=lxcs['PC-A11']),
        'PC_A2': LXC(name='PC-A21', template_context=lxcs['PC-A21']),
        'PC_B1': LXC(name='PC-B12', template_context=lxcs['PC-B12']),
        'PC_B2': LXC(name='PC-B22', template_context=lxcs['PC-B22']),
        'PC_C1': LXC(name='PC-C13', template_context=lxcs['PC-C13']),
        'PC_C2': LXC(name='PC-C23', template_context=lxcs['PC-C23']),
        'PC_D1': LXC(name='PC-D14', template_context=lxcs['PC-D14']),
        'PC_D2': LXC(name='PC-D24', template_context=lxcs['PC-D24']),
    }

    if context['ipsec_site2site']:    # Only FGT-A and FGT-B are used, FGT-C/D are not part of this scenario
        del(devices['FGT-C']); del(devices['FGT-D'])
        del(devices['PC_C1']); del(lxcs['PC-C13']); del(devices['PC_C2']); del(lxcs['PC-C23'])
        del(devices['PC_D1']); del(lxcs['PC-D14']); del(devices['PC_D2']); del(lxcs['PC-D24'])
        del(devices['Internet'])

    # Create poc
    poc = FortiPoCFoundation1(request, poc_id)
    poc.minimum_FOS_version = minimumFOSversion
    poc.messages = messages

    # Check request, render and deploy configs
    return fpoc.start(poc, devices)


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
    return fpoc.start(FortiPoCFoundation1(request, poc_id), devices)
