import copy

from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiPoC, FortiGate, LXC, VyOS, WAN, Interface, Network, FabricStudio


class FabricStudioOnce(FabricStudio):
    """
    """
    template_folder = 'FortiPoCOnce'
    mpls_summary = '10.71.0.0/16'  # mpls_summary assigned to the WAN of each FGT of this PoC
    password = 'Fortinet123#'  # password assigned to each FGT of this PoC

    devices = {
        # To be added
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info (from within fortipoc or from fortipoc public IP)
        super().__init__(request, poc_id)

        # Add password and MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate):
                device.password = self.password
                if device.wan is not None:
                    device.wan.mpls_summary = Network(self.mpls_summary)
