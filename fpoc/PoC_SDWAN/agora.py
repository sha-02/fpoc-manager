from django.core.handlers.wsgi import WSGIRequest
from fpoc.fortilab import FortiLab
from fpoc.devices import FortiGate, WAN, Interface, Network
from fpoc.fortilab import Mgmt
from fpoc.agora import SDW_agora

wan_DHCP = FortiGate(wan=WAN(
                    inet1=Interface(address='dhcp'),
                    inet2=Interface(address='dhcp'),
                    mpls1=Interface(address='dhcp'),
                    ))

# Define which physical FGT is assigned which role

WEST_DC1 = SDW_agora['SDW_1001F_A']
WEST_DC2 = SDW_agora['SDW_1001F_B']
EAST_DC1 = SDW_agora['SDW_3301E_A']

WEST_BR1 = SDW_agora['SDW_101F_A']
WEST_BR2 = SDW_agora['SDW_101F_B']

# EAST_BR1 = SDW_agora['SDW_3301E_B']
EAST_BR1 = SDW_agora['SDW_50G_A']
EAST_BR2 = SDW_agora['SDW_50G_B']


class AgoraSDWAN(FortiLab):
    """
    """
    template_folder = 'PoC_SDWAN'
    mgmt = Mgmt(vrfid=10, dns='96.45.45.45', gw='10.210.1.254')
    mpls_summary = '10.71.0.0/16'  # mpls_summary assigned to the WAN of each FGT of this PoC

    devices = impairment = {
        'WEST-DC1': WEST_DC1['impairment'],
        'WEST-DC2': WEST_DC2['impairment'],
        'EAST-DC1': EAST_DC1['impairment'],
        'WEST-BR1': WEST_BR1['impairment'],
        # 'WEST-BR1': WEST_BR1['impairment'].update(wan_DHCP),
        'WEST-BR2': WEST_BR2['impairment'],
        # 'WEST-BR2': WEST_BR2['impairment'].update(wan_DHCP),
        'EAST-BR1': EAST_BR1['impairment'],
        # 'EAST-BR1': EAST_BR1['impairment'].update(wan_DHCP),
        'EAST-BR2': EAST_BR2['impairment'],
        # 'EAST-BR2': EAST_BR2['impairment'].update(wan_DHCP),
    }

    no_impairment = {
        'WEST-DC1': WEST_DC1['no-impairment'],
        'WEST-DC2': WEST_DC2['no-impairment'],
        'EAST-DC1': EAST_DC1['no-impairment'],
        'WEST-BR1': WEST_BR1['no-impairment'],
        # 'WEST-BR1': WEST_BR1['no-impairment'].update(wan_DHCP),
        'WEST-BR2': WEST_BR2['no-impairment'],
        # 'WEST-BR2': WEST_BR2['no-impairment'].update(wan_DHCP),
        'EAST-BR1': EAST_BR1['no-impairment'],
        # 'EAST-BR1': EAST_BR1['no-impairment'].update(wan_DHCP),
        'EAST-BR2': EAST_BR2['no-impairment'],
        # 'EAST-BR2': EAST_BR2['no-impairment'].update(wan_DHCP),
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0, wan_impairment: bool = True):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info
        super().__init__(request, poc_id)

        # No impairment is requested
        if not wan_impairment:
            self.__class__.devices = self.__class__.no_impairment

        # Add MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate) and device.wan is not None:
                device.wan.mpls_summary = Network(self.__class__.mpls_summary)
