from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.shortcuts import render

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

APPNAME = "fpoc"


class HomePageView(TemplateView):
    template_name = f'{APPNAME}/home.html'


class AboutPageView(TemplateView):
    template_name = f'{APPNAME}/about.html'


def display_request_parameters(request: WSGIRequest):
    if request.method == 'POST':
        data = request.POST
    else:
        data = request.GET

    return render(request, f'{APPNAME}/display_request_parameters.html', {'method': request.method, 'params': data})
