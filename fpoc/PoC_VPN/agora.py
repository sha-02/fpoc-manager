from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import fpoc
from fpoc.fortilab import FortiLab
from fpoc.devices import Interface, FortiGate, LXC, VyOS, WAN
from fpoc.fortilab import Mgmt
from fpoc.agora import SDW_agora

# Define which physical FGT is assigned to FGT-A and to FGT-B

FGT_A = SDW_agora['SDW_1001F_A']['no-impairment']
FGT_B = SDW_agora['SDW_1001F_B']['no-impairment']


class FortiLabVpnSite2Site(FortiLab):
    """
    """
    template_folder = 'PoC_VPN'
    mgmt = Mgmt(vrfid=10, dns='96.45.45.45', gw='10.210.1.254')

    devices = {
        'FGT-A': FGT_A,
        'FGT-B': FGT_B,
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info (from within studio or from studio public IP)
        super(FortiLabVpnSite2Site, self).__init__(request, poc_id)


def vpn_site2site_fortilab(request: WSGIRequest, poc_id: int) -> HttpResponse:
    """
    Site-to-Site PoC for Hardware Lab
    """

    context = {
        'vpn': request.POST.get('vpn'),  # 'ipsec', 'gre', ...
        'routing': request.POST.get('routing'),  # 'static', 'ospf', 'ibgp', ...
        'ike': request.POST.get('ike'),  # 1 or 2
        'ipsec_phase1': request.POST.get('ipsec_phase1'),  # 'static2static', 'static2dialup'

        # Used as 'remote-gw' for IPsec tunnels
        'fgta_inet1': FGT_A.wan.inet1.ip,
        'fgta_inet2': FGT_A.wan.inet2.ip,
        'fgtb_inet1': FGT_B.wan.inet1.ip,
        'fgtb_inet2': FGT_B.wan.inet2.ip,
    }

    # If IPsec VPN with 'static2dialup' is selected then only static routing is possible
    if context['vpn'] == 'ipsec' and context['ipsec_phase1'] == 'static2dialup':
        context['routing'] = 'static'
    # 'static2dialup' only applies to pure IPsec VPN, not GRE-IPsec, not IP-IP-IPsec, etc...
    if context['ipsec_phase1'] == 'static2dialup' and context['vpn'] != 'ipsec':
        context['ipsec_phase1'] = 'static2static'  # force to 'static2static' if it's not pure IPsec VPN

    # List of all devices for this Scenario
    devices = {
        'FGT-A': FortiGate(name='FGT-A', lan=Interface(address='192.168.1.254/24'),
                           template_group='SITES',
                           template_context={'i': 1,
                                             'lan2': Interface(name='dummy',port=FGT_A.lan.port, vlanid=666, address='192.168.11.254/24', speed='auto'), # Dummy LAN2
                                             **context}),

        'FGT-B': FortiGate(name='FGT-B', lan=Interface(address='192.168.2.254/24'),
                           template_group='SITES',
                           template_context={'i': 2,
                                             'lan2': Interface(name='dummy',port=FGT_B.lan.port, vlanid=666, address='192.168.21.254/24', speed='auto'), # Dummy LAN2
                                             **context}),
    }

    # Check request, render and deploy configs
    return fpoc.start(FortiLabVpnSite2Site(request, poc_id), devices)
