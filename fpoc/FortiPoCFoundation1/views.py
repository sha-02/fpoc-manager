from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

from fpoc.fortios import fortios_firmware
from fpoc import FortiPoCFoundation1, FortiGate, LXC, Vyos, json_to_dict
from config.settings import BASE_DIR

#
# return render(request, 'fpoc/fpoc01/snr01/_FGT.conf', {'FGT': 'B'})
#######
# response = HttpResponse()
# template_ = loader.get_template('fpoc/fpoc01/snr01/_FGT.conf')
# context_ = Context({'FGT': 'A'})
# # template_rendered = template_.render(context_)
# template_rendered = template_.render({'FGT': 'A'})
# # return response.write(template_rendered)
# return HttpResponse(template_rendered)
#######

# def render_config_files(config_files):
#     output = '<html><pre>'
#     for config_file in config_files:
#         output += config_file + '=' * 100 + '<br>' * 2
#     output += '</pre></html>'
#
#     return output

APPNAME = "fpoc/FortiPoCFoundation1"


def fortipoc_VMs() -> dict:
    """
    Load the FortiPoC VM dictionary from JSON file
    :return: dict of FortiPoC VMs
    """
    return json_to_dict(f'{BASE_DIR}/fpoc/FortiPoCFoundation1/fortipoc_VM.json')


class HomePageView(TemplateView):
    template_name = f'{APPNAME}/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['firmware'] = fortios_firmware()
        context['fortipoc_VMs'] = fortipoc_VMs()
        context['fortigates'] = FortiPoCFoundation1.devices_of_type(FortiGate).keys()
        context['lxces'] = FortiPoCFoundation1.devices_of_type(LXC).keys()
        context['vyoses'] = FortiPoCFoundation1.devices_of_type(Vyos).keys()
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
