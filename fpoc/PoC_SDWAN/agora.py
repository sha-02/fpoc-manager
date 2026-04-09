from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiLab, FortiGate, WAN, Interface, Network
from fpoc.fortilab import Mgmt
from fpoc.agora import *

# Define each role for the PoC

WEST_DC1 = FortiGate(name='WEST-DC1',
                            wan=WAN(
                                # inet1=Interface(address='100.64.11.1/24'),
                                # inet2=Interface(address='100.64.12.1/24'),
                                # mpls1=Interface(address='10.71.14.1/24'),
                                inet1=Interface(address='100.64.71.1/24'),
                                inet2=Interface(address='100.64.72.1/24'),
                                mpls1=Interface(address='10.71.74.1/24'),
                            ))

WEST_DC2 = FortiGate(name='WEST-DC2',
                            wan=WAN(
                                # inet1=Interface(address='100.64.21.2/24'),
                                # inet2=Interface(address='100.64.22.2/24'),
                                # mpls1=Interface(address='10.71.24.2/24'),
                                inet1=Interface(address='100.64.71.2/24'),
                                inet2=Interface(address='100.64.72.2/24'),
                                mpls1=Interface(address='10.71.74.2/24'),
                            ))

EAST_DC1 = FortiGate(name='EAST-DC1',
                            wan=WAN(
                                # inet1=Interface(address='100.64.51.3/24'),
                                # inet2=Interface(address='100.64.52.3/24'),
                                # mpls1=Interface(address='10.71.54.3/24'),
                                inet1=Interface(address='100.64.71.3/24'),
                                inet2=Interface(address='100.64.72.3/24'),
                                mpls1=Interface(address='10.71.74.3/24'),
                            ))

EAST_BR1 = FortiGate(name='EAST-BR1',
                            wan=WAN(
                                inet1=Interface(address='dhcp'),
                                inet2=Interface(address='dhcp'),
                                mpls1=Interface(address='dhcp'),
                            ))

EAST_BR2 = FortiGate(name='EAST-BR2',
                            wan=WAN(
                                inet1=Interface(address='dhcp'),
                                inet2=Interface(address='dhcp'),
                                mpls1=Interface(address='dhcp'),
                            ))

WEST_BR1 = FortiGate(name='WEST-BR1',
                            wan=WAN(
                                inet1=Interface(address='dhcp'),
                                inet2=Interface(address='dhcp'),
                                mpls1=Interface(address='dhcp'),
                            ))

WEST_BR2 = FortiGate(name='WEST-BR2',
                            wan=WAN(
                                inet1=Interface(address='dhcp'),
                                inet2=Interface(address='dhcp'),
                                mpls1=Interface(address='dhcp'),
                            ))

# Define which physical FGT is assigned which role

WEST_DC1.update(SDW_1001F_A)
WEST_DC2.update(SDW_1001F_B)

WEST_BR1.update(SDW_101F_A)
WEST_BR2.update(SDW_101F_B)

EAST_DC1.update(SDW_3301E_A)
# EAST_BR1.update(SDW_3301E_B)
EAST_BR1.update(SDW_50G_A)
EAST_BR2.update(SDW_50G_B)


class AgoraSDWAN(FortiLab):
    """
    """
    template_folder = 'PoC_SDWAN'
    mgmt = Mgmt(vrfid=10, dns='96.45.45.45', gw='10.210.1.254')
    mpls_summary = '10.71.0.0/16'  # mpls_summary assigned to the WAN of each FGT of this PoC

    devices = {
        'WEST-DC1': WEST_DC1,
        'WEST-DC2': WEST_DC2,
        'EAST-DC1': EAST_DC1,
        'WEST-BR1': WEST_BR1,
        'WEST-BR2': WEST_BR2,
        'EAST-BR1': EAST_BR1,
        # 'EAST-BR2': EAST_BR2,
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info
        super().__init__(request, poc_id)

        # Add MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate) and device.wan is not None:
                device.wan.mpls_summary = Network(self.__class__.mpls_summary)
