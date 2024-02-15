from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

from fpoc.fortios import fortios_firmware
from fpoc.FortiPoCAirbus import FortiPoCAirbus
from fpoc import FortiGate, LXC, VyOS, fortipoc_VMs

APPNAME = "fpoc/FortiPoCAirbus"


class HomePageView(TemplateView):
    template_name = f'{APPNAME}/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['firmware'] = fortios_firmware()
        context['fortipoc_VMs'] = fortipoc_VMs()
        context['fortigates'] = FortiPoCAirbus.devices_of_type(FortiGate).keys()
        context['lxces'] = FortiPoCAirbus.devices_of_type(LXC).keys()
        context['vyoses'] = FortiPoCAirbus.devices_of_type(VyOS).keys()
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
