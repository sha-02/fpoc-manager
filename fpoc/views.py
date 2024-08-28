import threading

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import fpoc
from fpoc import FortiGate, FortiGate_HA, LXC, VyOS, fortios, FortiPoCFoundation1, FortiPoCSDWAN, FortiLabSDWAN
import fpoc.ansible as ansible

#
# Functions/Views which are common to multiple PoCs
#

def request_sanity(request: WSGIRequest) -> str:
    """
    If fpoc_manager is started from local host (i.e., does not run inside FortiPoC) then a FortiPoC instance must
    be specified
    """
    if not request.POST.get('targetedFOSversion'):
        return 'The FortiOS version must be specified'

    if '127.0.0.1' in request.get_host() and request.POST.get('pocInstance')=='0.0.0.0' \
            and request.POST['fpocIP'] == '' \
            and bool(request.POST.get('previewOnly', False)) == False:
        return "Select a PoC instance from the list, 'internal' is not a valid choice from 127.0.0.1"

    return ''


def bootstrap(request: WSGIRequest) -> HttpResponse:
    """
    """

    # Check the request
    error_message = request_sanity(request)
    if error_message:
        return render(request, f'fpoc/message.html',{'title': 'Error', 'header': 'Error', 'message': error_message})


    # Create a class instance based on the class name stored as a string in variable request.POST['Class_PoC']
    # eval() is used to "convert" the string into a class name which can be instantiated with (request=..., poc_id=...)
    poc = eval(request.POST['Class_PoC'])(request=request, poc_id=0)

    fortigates = poc.devices_of_type(FortiGate)  # All FortiGate devices

    for fpoc_fgtname, fortigate in fortigates.items():
        fortigate.template_filename = request.POST.get('targetedFOSversion') + '.conf'  # e.g. '6.4.6.conf'

        fortigate.template_context = {'name': fpoc_fgtname, 'mgmt': poc.devices[fpoc_fgtname].mgmt}
        if bool(request.POST.get('WAN_underlays', False)) and fortigate.wan is not None:
            fortigate.template_context['WAN_underlays'] = True
            fortigate.template_context['wan'] = fortigate.wan
        else:
            fortigate.template_context['WAN_underlays'] = False

        if request.POST.get('HA') == 'FGCP':
            fortigate.HA = FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, group_id=1, group_name=fpoc_fgtname,
                                     hbdev=[('port6', 0)], sessyncdev=['port6'],
                                     monitordev=['port1', 'port2', 'port5'], priority=128)
            if fpoc_fgtname in ('FGT-A_sec', 'FGT-B_sec', 'FGT-C_sec', 'FGT-D_sec'):
                fortigate.HA.role = FortiGate_HA.Roles.SECONDARY
            else:
                fortigate.HA.role = FortiGate_HA.Roles.PRIMARY

    # Render and deploy the configs
    return fpoc.start(poc, fortigates)


def upgrade(request: WSGIRequest) -> HttpResponse:
    """
    """

    # Check the request
    error_message = request_sanity(request)
    if error_message:
        return render(request, f'fpoc/message.html',{'title': 'Error', 'header': 'Error', 'message': error_message})

    fos_version_target = request.POST.get('targetedFOSversion')

    # Create a class instance based on the class name stored as a string in variable request.POST['Class_PoC']
    # eval() is used to "convert" the string into a class name which can be instantiated with (request=..., poc_id=...)
    poc = eval(request.POST['Class_PoC'])(request=request, poc_id=None)

    # the intersection of the keys of request.POST dict and the foundation1 dict keys produces the keys of each
    # device to be upgraded
    fortigates = poc.devices_of_type(FortiGate)  # All FortiGate devices
    fortigates = sorted(list(request.POST.keys() & fortigates.keys()))

    if request.POST.get('previewOnly'):
        return render(request, f'fpoc/message.html',
                      {'title': 'Upgrade', 'header': 'Upgrade preview', 'message': fortigates})

    def _upgrade_fgt(device: FortiGate, fos_target: str, lock: threading.Lock):
        fortios.prepare_api(device)  # create API admin and key if needed
        device.fos_version = fortios.retrieve_fos_version(device)  # Update info about the version running on FGT (string, for e.g. '7.2.5')
        if fos_version_target != device.fos_version:
            print(f"{device.name} : FGT is running FOS {device.fos_version}", end='')
            print(f" but user requested FOS {fos_version_target}: need to update the FOS version")
            fortios.update_fortios_version(device, fos_target, lock)  # Upgrade/Downgrade FortiGate
        else:
            print(f"{device.name} : FGT is already running FOS {device.fos_version}. No upgrade needed.")

    # Only keep the 'devices' that are active members for the poc
    poc.members(devnames=fortigates)

    threads = list()
    for fgt in poc:
        print(f'{fgt.name} : Upgrading to FortiOS', fos_version_target, ' ...')
        thread = threading.Thread(target=_upgrade_fgt, args=(fgt, fos_version_target, poc.lock))
        threads.append(thread)
        thread.start()

    for index, thread in enumerate(threads):
        thread.join()

    return render(request, f'fpoc/message.html',
                  {'title': 'Upgrade', 'header': 'Upgrade status', 'message': fortigates})



def poweron(request: WSGIRequest) -> HttpResponse:
    """
    """

    # Create a class instance based on the class name stored as a string in variable request.POST['Class_PoC']
    # eval() is used to "convert" the string into a class name which can be instantiated with (request=..., poc_id=...)
    poc = eval(request.POST['Class_PoC'])(request=request, poc_id=None)

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


