from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

from fpoc.fortios import fortios_firmware
from fpoc.FortiPoCSDWAN import FortiPoCSDWAN
from fpoc import FortiGate, LXC, VyOS, fortipoc_VMs

APPNAME = "fpoc/FortiPoCSDWAN"


class HomePageView(TemplateView):
    # template_name = f'{APPNAME}/home.html'

    def get_template_names(self):
        if 'ADVPNv2' in self.request.path:
            template_name = f'{APPNAME}/home2.html'
        else:
            template_name = f'{APPNAME}/home.html'

        return [template_name]

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['fortigates'] = FortiPoCSDWAN.devices_of_type(FortiGate).keys()
        context['lxces'] = FortiPoCSDWAN.devices_of_type(LXC).keys()
        context['vyoses'] = FortiPoCSDWAN.devices_of_type(VyOS).keys()
        context['fortipoc_VMs'] = fortipoc_VMs()
        minmum_fortios = '7.4.4' if 'ADVPNv2' in self.request.path else '7.0.0'
        context['firmware'] = fortios_firmware(minmum_fortios)
        return context


class AboutPageView(TemplateView):
    template_name = f'{APPNAME}/about.html'


def display_request_parameters(request: WSGIRequest):
    """
    """
    if request.method == 'POST':
        data = request.POST
    else:
        data = request.GET

    return render(request, f'{APPNAME}/display_request_parameters.html', {'method': request.method, 'params': data})
