import copy

from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

from fpoc.fortios import fortios_firmware
from fpoc.PoC_SDWAN import AgoraSDWAN, SDWAN1, SDWAN2, SDWAN3 # required for eval(context['Class_PoC'])
from fpoc.devices import FortiGate, LXC, VyOS
from fpoc.studio_instances import studio_instances

APPNAME = "fpoc/PoC_SDWAN"


class HomePageView(TemplateView):
    # template_name = f'{APPNAME}/home.html'

    def get_template_names(self):
        template_name = f'{APPNAME}/home.html'
        if '7.6_8.0' in self.request.path:
            template_name = f'{APPNAME}/home3.html'
        elif '7.4_7.6' in self.request.path:
            template_name = f'{APPNAME}/home2.html'

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

        # Add VM Studio instances (eg, almodo10,...) to context if applicable
        context['studio_instances'] = False
        if 'fabric' in self.request.path:
            context['studio_instances'] = studio_instances()

        # List of devices for the PoC
        if 'fabric' in self.request.path:
            context['Class_PoC'] = 'FabricStudioSDWAN'  # passes the class to the common views (bootstrap, upgrade, poweron) via the form
            context['lxces'] = eval(context['Class_PoC']).devices_of_type(LXC).keys()
            context['vyoses'] = eval(context['Class_PoC']).devices_of_type(VyOS).keys()

            # Device names in the class are generic (HUB1, HUB2,..) while they are specific in the poc (WEST-DC1,...)
            # A mapping dict is used to map the poc devname with the class devname
            mapping={}
            if '7.6_8.0' in self.request.path:
                mapping = fpoc.PoC_SDWAN.sdwan3.mapping
            elif '7.4_7.6' in self.request.path:
                mapping = fpoc.PoC_SDWAN.sdwan2.mapping
            elif '7.0_7.2' in self.request.path:
                mapping = fpoc.PoC_SDWAN.sdwan1.mapping

            fgt_keys = eval(context['Class_PoC']).devices_of_type(FortiGate).keys() # eg dict_keys(['HUB1', 'HUB2', ...])
            reverse_mapping = {v: k for k, v in mapping.items()} # use the mapping dict to change the keys to...
            context['fortigates'] = [reverse_mapping[k] for k in fgt_keys]  # ... ['WEST-DC1', 'WEST-DC2', ...]

        if 'hardware' in self.request.path:
            context['Class_PoC'] = 'AgoraSDWAN'  # passes the class to the common views (bootstrap, upgrade, poweron) via the form
            context['fortigates'] = eval(context['Class_PoC']).devices_of_type(FortiGate).keys()

        # Defines the minimum FOS version proposed in the dropdown list
        minimum_fortios = '7.0.0'
        if '7.6_8.0' in self.request.path:
            minimum_fortios = '7.6.7'
        elif '7.4_7.6' in self.request.path:
            minimum_fortios = '7.4.4'

        context['firmware'] = fortios_firmware(minimum_fortios)

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
