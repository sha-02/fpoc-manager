from django.core.handlers.wsgi import WSGIRequest
from fpoc.fortilab import FortiLab
from fpoc.devices import FortiGate, Network
from fpoc.fortilab import Mgmt
from fpoc.agora import SDW_agora

class AgoraSDWAN(FortiLab):
    """
    """
    template_folder = 'PoC_SDWAN'
    mgmt = FortiLab.mgmt.update(Mgmt(dns='96.45.45.45', gw='10.210.1.254'))
    mpls_summary = '10.71.0.0/16'  # mpls_summary assigned to the WAN of each FGT of this PoC

    devices = impairment = {phy_name: SDW_agora[phy_name]['impairment'] for phy_name in SDW_agora.keys()}
    no_impairment = {phy_name: SDW_agora[phy_name]['no-impairment'] for phy_name in SDW_agora.keys()}

    def __init__(self, request: WSGIRequest, poc_id: int = 0, wan_impairment: bool = True):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info
        super().__init__(request, poc_id)

        # Set impairment for the class devices
        if wan_impairment:
            type(self).devices = type(self).impairment
        else:
            type(self).devices = type(self).no_impairment

        # Add MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate) and device.wan is not None:
                device.wan.mpls_summary = Network(type(self).mpls_summary)

    def members(self, devices: dict = None, devnames: list = None):
        """
        only keep some devices
        for each device which is kept: merge the class-level attributes with the instance-level attributes
        """
        # Call parent class to do the device filtering and the class-level/device-level attribute merge
        super().members(devices, devnames)

        # configure access attributes for each device (name, IP@, SSH/HTTPS ports) depending on whether it is accessed
        # directly or via an external DNAT/VIP
        for key_name, device in self.devices.items():
            device.name_phy = device.name_phy or key_name   # init to 'key_name' if 'name_phy' is None
            device.name = device.name or device.name_phy  # init to 'name_phy' if 'name' is None
            if device.vip_access is None:  # device is accessed directly via its mgmt interface IP
                device.ip = device.mgmt.ip
                device.https_port = 443
                device.ssh_port = 22
            else:  # device is accessed indirectly via DNAT/VIP
                device.ip = device.vip_access.ip
                device.https_port = device.vip_access.https_port
                device.ssh_port = device.vip_access.ssh_port
