from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render

from fpoc.devices import FortiGate
from fpoc.deploy import device_URL, device_URL_console
from fpoc.PoC_SDWAN import AgoraSDWAN, FabricStudioSDWAN, SDWAN1, SDWAN2, SDWAN3    # Required for  eval(request.POST['Class_PoC'])


def dashboard(request: WSGIRequest) -> HttpResponse:
    """
    Display a dashboard of all devices
    """

    # Check the request
    # error_message = request_sanity(request)
    # if error_message:
    #     return render(request, f'fpoc/message.html',{'title': 'Error', 'header': 'Error', 'message': error_message})

    # Create a class instance based on the class name stored as a string in variable request.POST['Class_PoC']
    # eval() is used to "convert" the string into a class name which can be instantiated with (request=..., poc_id=...)
    poc = eval(request.POST['Class_PoC'])(request=request, poc_id=0)
    device_names = eval(request.POST['Class_PoC']).devices_of_type(FortiGate).keys()

    # the intersection of the keys of request.POST dict and the keys of poc.devices dict produces the keys of each
    # device to be listed in the dashboard
    # device_names = list(poc.request.POST.keys() & poc.devices.keys())
    device_names = list(poc.request.POST.keys() & device_names)    # 'WEST-DC1',...
    device_names.sort()

    # Only keep the desired 'devices' (this call allows to fill attributes for the devices like ip, etc...)
    poc.members(devnames=device_names)

    devices = {'WEST': list(), 'EAST': list()}
    for devname in device_names:
        region = 'WEST'
        if 'EAST' in devname:
            region='EAST'

        devices[region].append({
            'name': devname,
            'name_phy': poc.devices[devname].name_phy,
            'URL': device_URL(poc, poc.devices[devname]),
            'console': device_URL_console(poc, poc.devices[devname])
        })

    # Render and deploy the dashboard
    return render(poc.request, f'fpoc/{poc.template_folder}/dashboard.html', {'devices': devices})
