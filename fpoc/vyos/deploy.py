from django.core.handlers.wsgi import WSGIRequest
from django.template import loader
from config.settings import BASE_DIR

import fpoc.fortipoc as fortipoc
from fpoc.devices import Vyos
from fpoc.exceptions import StopProcessingDevice, ReProcessDevice
from fpoc.fortipoc import TypePoC

def deploy(request: WSGIRequest, poc: TypePoC, device: Vyos):
    """
    Render the configuration (Django template) and deploy it

    :param request:
    :param scenario:
    :param device:
    :return:
    """

