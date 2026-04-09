from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiGate, LXC, VyOS, WAN, Interface
from fpoc.PoC_SDWAN import FabricStudioSDWAN


class StudioVPN(FabricStudioSDWAN):
    """
    """
    template_folder = 'PoC_VPN'

    devices = {
        'FGT-A': FabricStudioSDWAN.devices['WEST-DC1'],
        'FGT-B': FabricStudioSDWAN.devices['WEST-DC2'],
        'FGT-C': FabricStudioSDWAN.devices['WEST-BR1'],
        'FGT-D': FabricStudioSDWAN.devices['WEST-BR2'],
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info (from within studio or from studio public IP)
        super().__init__(request, poc_id)

        # Add password to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate):
                device.password = self.password
