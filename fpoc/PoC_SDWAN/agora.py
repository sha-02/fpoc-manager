from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiLab, FortiGate, WAN, Interface, Network
from fpoc.fortilab import Mgmt
from fpoc.agora import SDW_agora

wan_DHCP = FortiGate(wan=WAN(
                    inet1=Interface(address='dhcp'),
                    inet2=Interface(address='dhcp'),
                    mpls1=Interface(address='dhcp'),
                    ))

# Define which physical FGT is assigned which role

WEST_DC1 = SDW_agora['SDW_1001F_A']['no-impairment']
WEST_DC2 = SDW_agora['SDW_1001F_B']['no-impairment']
EAST_DC1 = SDW_agora['SDW_3301E_A']['no-impairment']

WEST_BR1 = SDW_agora['SDW_101F_A']['no-impairment'].update(wan_DHCP)
WEST_BR2 = SDW_agora['SDW_101F_B']['no-impairment'].update(wan_DHCP)

# EAST_BR1 = SDW_agora['SDW_3301E_B']['no-impairment'].update(wan_DHCP)
EAST_BR1 = SDW_agora['SDW_50G_A']['no-impairment'].update(wan_DHCP)
EAST_BR2 = SDW_agora['SDW_50G_B']['no-impairment'].update(wan_DHCP)


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
