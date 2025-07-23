import copy

from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

from fpoc.fortios import fortios_firmware
from fpoc.FortiPoCSDWAN import FortiPoCSDWAN, FortiLabSDWAN, FabricStudioSDWAN
from fpoc import FortiGate, LXC, VyOS, fortipoc_instances

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

        # Build the home page with a selection of all the sites URL which starts with "SDWAN/"
        # sdwan_sites = { k: v for k, v in kwargs['sites'].items() if k.startswith('SDWAN/') }
        sdwan_sites = copy.deepcopy(kwargs['sites'])

        # Set the current site to 'selected' after having unselected all other sites
        for site in sdwan_sites.values():
            site['selected'] = False
        sdwan_sites[self.request.path[1:]]['selected'] = True

        context['sdwan_sites'] = sdwan_sites

        # Add FortiPoC instances (eg, almodo10,...) to context if applicable
        context['fortipoc_instances'] = False
        if 'fortipoc' in self.request.path or 'fabric' in self.request.path:
            context['fortipoc_instances'] = fortipoc_instances()

        minmum_fortios = '7.4.4' if 'ADVPNv2' in self.request.path else '7.0.0'
        context['firmware'] = fortios_firmware(minmum_fortios)

        # List of devices for the PoC
        if 'fortipoc' in self.request.path:
            context['Class_PoC'] = 'FortiPoCSDWAN'  # passes the class to the common views (bootstrap, upgrade, poweron) via the form
            context['fortigates'] = FortiPoCSDWAN.devices_of_type(FortiGate).keys()
            context['lxces'] = FortiPoCSDWAN.devices_of_type(LXC).keys()
            context['vyoses'] = FortiPoCSDWAN.devices_of_type(VyOS).keys()

        if 'fabric' in self.request.path:
            context['Class_PoC'] = 'FabricStudioSDWAN'  # passes the class to the common views (bootstrap, upgrade, poweron) via the form
            context['fortigates'] = FabricStudioSDWAN.devices_of_type(FortiGate).keys()
            context['lxces'] = FabricStudioSDWAN.devices_of_type(LXC).keys()
            context['vyoses'] = FabricStudioSDWAN.devices_of_type(VyOS).keys()

        if 'hardware' in self.request.path:
            context['Class_PoC'] = 'FortiLabSDWAN'  # passes the class to the common views (bootstrap, upgrade, poweron) via the form
            context['fortigates'] = FortiLabSDWAN.devices_of_type(FortiGate).keys()

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
