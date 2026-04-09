from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

from fpoc.fortios import fortios_firmware
from fpoc import FortiGate, LXC, VyOS, studio_instances
from .poc import PoCOnce

APPNAME = "fpoc/PoC_Once"


class HomePageView(TemplateView):
    template_name = f'{APPNAME}/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)

        context['Class_PoC'] = 'PoCOnce'  # passes the class to the common views (bootstrap, upgrade, poweron) via the form
        context['fortigates'] = eval(context['Class_PoC']).devices_of_type(FortiGate).keys()
        context['firmware'] = fortios_firmware()
        context['studio_instances'] = studio_instances()
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
