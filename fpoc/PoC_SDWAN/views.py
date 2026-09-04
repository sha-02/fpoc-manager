import copy

from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

from fpoc.fortios import fortios_firmware
from fpoc.devices import FortiGate, LXC, VyOS
from fpoc.studio_instances import studio_instances

# required for eval(context['Class_PoC']) ======================================
from fpoc.PoC_SDWAN import AgoraSDWAN, SDWAN1, SDWAN2, SDWAN3, SDWAN3_Agora
# ==============================================================================

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

        # context contains: 'sites' dict()
        # which is inherited from the call in config.urls

        # Add current path to the context
        context['current_path'] = self.request.path

        # Add VM Studio instances (eg, almodo10,...) to context if applicable
        context['studio_instances'] = False
        if 'fabric' in self.request.path:
            context['studio_instances'] = studio_instances()

        # Add agora to context if applicable
        context['agora'] = 'agora' in self.request.path

        # List of devices for the PoC
        if 'fabric' in self.request.path:
            if '7.6_8.0' in self.request.path:  # passes the class via the form
                context['Class_PoC'] = 'SDWAN3'
            elif '7.4_7.6' in self.request.path:
                context['Class_PoC'] = 'SDWAN2'
            elif '7.0_7.2' in self.request.path:
                context['Class_PoC'] = 'SDWAN1'

            # List of devices to be displayed
            context['fortigates'] = eval(context['Class_PoC']).devices_of_type(FortiGate).keys()
            context['lxces'] = eval(context['Class_PoC']).devices_of_type(LXC).keys()
            context['vyoses'] = eval(context['Class_PoC']).devices_of_type(VyOS).keys()

        if 'agora' in self.request.path:
            if '7.6_8.0' in self.request.path:  # passes the class via the form
                context['Class_PoC'] = 'SDWAN3_Agora'
            else:
                context['Class_PoC'] = 'AgoraSDWAN'  # passes the class via the form
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
