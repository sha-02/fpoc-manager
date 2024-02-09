import threading

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import fpoc
from fpoc import FortiGate, FortiGate_HA, LXC, VyOS, fortios
import fpoc.ansible as ansible


def upgrade(request: WSGIRequest, Class_PoC) -> HttpResponse:
    """
    """
    fos_version_target = request.POST.get('targetedFOSversion')
    if not fos_version_target:
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': 'FortiOS version must be provided'})

    poc = Class_PoC(request=request, poc_id=None)

    # the intersection of the keys of request.POST dict and the foundation1 dict keys produces the keys of each
    # device to be upgraded
    fortigates = poc.devices_of_type(FortiGate)  # All FortiGate devices
    fortigates = sorted(list(request.POST.keys() & fortigates.keys()))

    if request.POST.get('previewOnly'):
        return render(request, f'fpoc/message.html',
                      {'title': 'Upgrade', 'header': 'Upgrade preview', 'message': fortigates})

    def _upgrade_fgt(device: FortiGate, fos_target: str, lock: threading.Lock):
        fortios.prepare_api(device)  # create API admin and key if needed
        fortios.update_fortios_version(device, fos_target, lock)  # Upgrade/Downgrade FortiGate

    # Only keep the 'devices' that are active members for the poc
    poc.members(devnames=fortigates)

    threads = list()
    for fgt in poc:
        print(f'{fgt.name} : Upgrading to FortiOS', request.POST.get('targetedFOSversion'), ' ...')
        thread = threading.Thread(target=_upgrade_fgt, args=(fgt, fos_version_target, poc.lock))
        threads.append(thread)
        thread.start()

    for index, thread in enumerate(threads):
        thread.join()

    return render(request, f'fpoc/message.html',
                  {'title': 'Upgrade', 'header': 'Upgrade status', 'message': fortigates})


def poweron(request: WSGIRequest, Class_PoC) -> HttpResponse:
    """
    """
    poc = Class_PoC(request=request, poc_id=None)

    devices = poc.devices_of_type(FortiGate)  # All FortiGate devices
    devices.update(poc.devices_of_type(LXC))  # + all LXC devices
    devices.update(poc.devices_of_type(VyOS))  # + all VyOS devices

    # the intersection of the keys of request.POST dict and the TypePoC dict keys produces the keys of each
    # device to be powered on
    devices_to_start = sorted(list(request.POST.keys() & devices.keys()))

    if request.POST.get('previewOnly'):
        return render(request, f'fpoc/message.html',
                      {'title': 'Power-On', 'header': 'Power-On preview', 'message': devices_to_start})

    # TODO: admin & pwd should be stored in DB so that it can be customized per FortiPoC (like WAN_CTRL)
    _, result = ansible.poweron_devices(devices_to_start, host=poc.ip, admin='admin', pwd='')
    result = '<pre> ' + result + ' </pre>'

    return render(request, f'fpoc/message.html',
                  {'title': 'Power-On', 'header': 'Power-On status', 'message': result})


def bootstrap(request: WSGIRequest, Class_PoC) -> HttpResponse:
    """
    """
    # Check the request
    if not request.POST.get('targetedFOSversion'):
        return render(request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': 'The FortiOS version must be specified'})

    poc = Class_PoC(request=request, poc_id=0)

    fortigates = poc.devices_of_type(FortiGate)  # All FortiGate devices

    for fpoc_fgtname, fortigate in fortigates.items():
        fortigate.template_filename = request.POST.get('targetedFOSversion') + '.conf'  # e.g. '6.4.6.conf'

        fortigate.template_context = {'name': fpoc_fgtname, 'mgmt': poc.devices[fpoc_fgtname].mgmt}
        if bool(request.POST.get('WAN_underlays', False)) and fortigate.wan is not None:
            fortigate.template_context['WAN_underlays'] = True
            fortigate.template_context['wan'] = fortigate.wan
            fortigate.template_context['ip_lastbyte'] = fortigate.offset + 1
        else:
            fortigate.template_context['WAN_underlays'] = False

        if request.POST.get('HA') == 'FGCP':
            fortigate.ha = FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, group_id=1, group_name=fpoc_fgtname,
                                     hbdev=[('port6', 0)], sessyncdev=['port6'],
                                     monitordev=['port1', 'port2', 'port5'], priority=128)
            if fpoc_fgtname in ('FGT-A_sec', 'FGT-B_sec', 'FGT-C_sec', 'FGT-D_sec'):
                fortigate.ha.role = FortiGate_HA.Roles.SECONDARY
            else:
                fortigate.ha.role = FortiGate_HA.Roles.PRIMARY

    # Only keep the 'devices' that are active members for the poc
    # poc.members(devices=fortigates)

    # Render and deploy the configs
    return fpoc.start(poc, fortigates)
