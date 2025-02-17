from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.http import HttpResponse

import fpoc
from fpoc.fortilab import FortiLab
from fpoc.devices import Interface, FortiGate, LXC, VyOS, WAN
from fpoc.FortiPoCFoundation1 import FortiPoCFoundation1

# Define each physical FGT in the hardware Lab

SDW_1001F_A = FortiGate(name_fpoc='SDW-1001F-A', alias='SDW-1001F-A', model='FGT_1001F', password='fortinet',
                        npu='NP7', reboot_delay=200,
                        mgmt=Interface('mgmt', 0, '10.210.0.59/23'),
                        lan=Interface('port6', vlanid=0, speed='1000auto'),
                        wan=WAN(
                            inet1=Interface('port1', vlanid=0, speed='1000auto'),
                            inet2=Interface('port2', vlanid=0, speed='1000auto'),
                            mpls1=Interface('port4', vlanid=0, speed='1000auto'),
                        ))

SDW_1001F_B = FortiGate(name_fpoc='SDW-1001F-B', alias='SDW-1001F-B', model='FGT_1001F', password='fortinet',
                        npu='NP7', reboot_delay=200,
                        mgmt=Interface('mgmt', 0, '10.210.0.50/23'),
                        lan=Interface('port6', vlanid=0, speed='1000auto'),
                        wan=WAN(
                            inet1=Interface('port1', vlanid=0, speed='1000auto'),
                            inet2=Interface('port2', vlanid=0, speed='1000auto'),
                            mpls1=Interface('port4', vlanid=0, speed='1000auto'),
                        ))

SDW_3301E_A = FortiGate(name_fpoc='SDW-3301E-A', alias='SDW-3301E-A', model='FGT_3301E', password='fortinet',
                        npu='NP6', reboot_delay=200,
                        mgmt=Interface('mgmt1', 0, '10.210.0.63/23'),
                        lan=Interface('port5', vlanid=0, speed='1000auto'),
                        wan=WAN(
                            inet1=Interface('port1', vlanid=0, speed='1000auto'),
                            inet2=Interface('port2', vlanid=0, speed='1000auto'),
                            mpls1=Interface('port4', vlanid=0, speed='1000auto'),
                        ))

SDW_3301E_B = FortiGate(name_fpoc='SDW-3301E-B', alias='SDW-3301E-B', model='FGT_3301E', password='fortinet',
                        npu='NP6', reboot_delay=200,
                        mgmt=Interface('mgmt1', 0, '10.210.0.67/23'),
                        lan=Interface('port5', vlanid=0, speed='1000auto'),
                        wan=WAN(
                            inet1=Interface('port1', vlanid=0, speed='1000auto'),
                            inet2=Interface('port2', vlanid=0, speed='1000auto'),
                            mpls1=Interface('port4', vlanid=0, speed='1000auto'),
                        ))

SDW_101F_A = FortiGate(name_fpoc='SDW-101F-A', alias='SDW-101F-A', model='FGT_101F', password='fortinet',
                       npu='SoC4', reboot_delay=150,
                       mgmt=Interface('mgmt', 0, '10.210.0.23/23'),
                       lan=Interface('port4', vlanid=0, speed='auto'),
                       wan=WAN(
                           inet1=Interface('wan1', vlanid=0, speed='auto'),
                           inet2=Interface('port1', vlanid=0, speed='auto'),
                           mpls1=Interface('port2', vlanid=0, speed='auto'),
                       ))

SDW_101F_B = FortiGate(name_fpoc='SDW-101F-B', alias='SDW-101F-B', model='FGT_101F', password='fortinet',
                       npu='SoC4', reboot_delay=150,
                       mgmt=Interface('mgmt', 0, '10.210.0.41/23'),
                       lan=Interface('port4', vlanid=0, speed='auto'),
                       wan=WAN(
                           inet1=Interface('port1', vlanid=0, speed='auto'),
                           inet2=Interface('port2', vlanid=0, speed='auto'),
                           mpls1=Interface('wan1', vlanid=0, speed='auto'),
                       ))

# Update with the underlay IP addresses

SDW_1001F_A.update(FortiGate(wan=WAN(
    inet1=Interface(address='100.64.11.1/24'),
    inet2=Interface(address='100.64.12.1/24'),
    mpls1=Interface(address='10.71.14.1/24'),
)))

SDW_1001F_B.update(FortiGate(wan=WAN(
    inet1=Interface(address='100.64.21.2/24'),
    inet2=Interface(address='100.64.22.2/24'),
    mpls1=Interface(address='10.71.24.2/24'),
)))

SDW_3301E_A.update(FortiGate(wan=WAN(
    inet1=Interface(address='100.64.51.3/24'),
    inet2=Interface(address='100.64.52.3/24'),
    mpls1=Interface(address='10.71.54.3/24'),
)))

SDW_3301E_B.update(FortiGate(wan=WAN(
    inet1=Interface(address='dhcp'),
    inet2=Interface(address='dhcp'),
    mpls1=Interface(address='dhcp'),
)))

SDW_101F_A.update(FortiGate(wan=WAN(
    inet1=Interface(address='dhcp'),
    inet2=Interface(address='dhcp'),
    mpls1=Interface(address='dhcp'),
)))

SDW_101F_B.update(FortiGate(wan=WAN(
    inet1=Interface(address='dhcp'),
    inet2=Interface(address='dhcp'),
    mpls1=Interface(address='dhcp'),
)))

# Define which physical FGT is assigned to FGT-A and to FGT-B

FGT_A = SDW_1001F_A
FGT_B = SDW_1001F_B

# SDW_101F_A.wan.inet1.update(Interface(address='100.64.31.1/24'))
# SDW_101F_A.wan.inet2.update(Interface(address='100.64.32.1/24'))
# FGT_B = SDW_101F_A


class FortiLabVpnSite2Site(FortiLab):
    """
    """
    template_folder = 'FortiPoCFoundation1'
    mgmt_gw = '10.210.1.254'  # Gateway for OOB mgmt network
    mgmt_dns = '96.45.45.45'  # DNS from the OOB mgmt
    mgmt_vrf = 10

    devices = {
        'FGT-A': FGT_A,
        'FGT-B': FGT_B,
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info (from within fortipoc or from fortipoc public IP)
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
