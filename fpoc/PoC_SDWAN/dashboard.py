from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render

from fpoc.devices import FortiGate
from fpoc.deploy import device_URL, device_URL_console
from fpoc.PoC_SDWAN import AgoraSDWAN, FabricStudioSDWAN    # Required for  eval(request.POST['Class_PoC'])
import fpoc.PoC_SDWAN.sdwan2, fpoc.PoC_SDWAN.sdwan3

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
    poc = eval(request.POST['Class_PoC'])(request=request, poc_id=0)    # dict keys 'HUB1',...

    # Device names in the class are phy_names (HUB1, HUB2,..) while they are specific in the poc (WEST-DC1,...)
    # A mapping dict is used to map the poc devname with the class phyname
    mapping = {}
    if '7.6_8.0' in request.path:
        mapping = fpoc.PoC_SDWAN.sdwan3.mapping
    elif '7.4_7.6' in request.path:
        mapping = fpoc.PoC_SDWAN.sdwan2.mapping

    phy_names = poc.devices_of_type(FortiGate).keys()  # eg dict_keys(['HUB1', 'HUB2', ...])
    reverse_mapping = {v: k for k, v in mapping.items()}  # use the mapping dict to change the keys to...
    device_names = [reverse_mapping[k] for k in phy_names]  # ... ['WEST-DC1', 'WEST-DC2', ...]

    # the intersection of the keys of request.POST dict and the keys of poc.devices dict produces the keys of each
    # device to be listed in the dashboard
    # device_names = list(poc.request.POST.keys() & poc.devices.keys())
    device_names = list(poc.request.POST.keys() & device_names)    # 'WEST-DC1',...
    device_names.sort()

    # Now that we know the poc devices ('WEST-DC1',...) to display on the dashboard
    # we need to switch back to phy_names
    phy_names = [mapping[k] for k in device_names]  # ... ['HUB1', 'HUB2', ...]

    # Only keep the desired 'devices' (this call allows to fill attributes for the devices like ip, etc...)
    poc.members(devnames=phy_names)

    devices = {'WEST': list(), 'EAST': list()}
    for devname in device_names:
        region = 'WEST'
        if 'EAST' in devname:
            region='EAST'

        devices[region].append({
            'name': devname,
            'name_phy': poc.devices[mapping[devname]].name_phy,
            'URL': device_URL(poc, poc.devices[mapping[devname]]),
            'console': device_URL_console(poc, poc.devices[mapping[devname]])
        })

    # Render and deploy the dashboard
    return render(poc.request, f'fpoc/{poc.template_folder}/dashboard.html', {'devices': devices})
