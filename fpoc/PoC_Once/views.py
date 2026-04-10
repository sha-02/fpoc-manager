from ansible_collections.ansible.posix.plugins.action.synchronize import PODMAN
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

from fpoc.fortios import fortios_firmware
from fpoc import studio_instances

######### CURRENT POC = POC01  ##############################################
from .once01 import devices
POC_ID=1
#############################################################################

APPNAME = "fpoc/PoC_Once"


class HomePageView(TemplateView):
    template_name = f'{APPNAME}/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['poc_id']= POC_ID
        context['fortigates'] = devices
        context['studio_instances'] = studio_instances()
        context['firmware'] = fortios_firmware()
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
