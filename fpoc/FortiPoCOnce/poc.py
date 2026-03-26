from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import copy

import fpoc
from fpoc import AbortDeployment
from fpoc.devices import Interface, FortiGate, LXC
from fpoc.FortiPoCSDWAN import FortiPoCSDWAN, FortiLabSDWAN, FabricStudioSDWAN
from fpoc.typing import TypePoC
import typing

import ipaddress


def poc(request: WSGIRequest) -> HttpResponse:
    return render(request, f'fpoc/message.html',
                  {'title': 'PoC', 'header': 'PoC', 'message': "One-Off PoC to build"})