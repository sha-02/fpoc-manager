from django.core.handlers.wsgi import WSGIRequest
from django.template import loader

import fpoc.ssh
from fpoc import TypePoC, Vyos

def deploy(request: WSGIRequest, poc: TypePoC, device: Vyos):
    """
    Render the configuration (Django template) and deploy it

    :param request:
    :param poc:
    :param device:
    :return:
    """
