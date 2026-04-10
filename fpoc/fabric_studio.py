from django.core.handlers.wsgi import WSGIRequest

from fpoc import FortiLab
from fpoc.devices import FortiGate
from fpoc.fortilab import Mgmt


class FabricStudio(FortiLab):
    # BASE_PORT_HTTPS = 13000  # default HTTPS ports for FabricStudio devices
    # Fabric Studio has a reverse proxy which blocks API call on the default HTTPS redirection ports (13000 + devid)
    # So I configured additional HTTPS redirections with a base port of 20000
    BASE_PORT_HTTPS = 20000
    BASE_PORT_SSH = 11000

    mgmt = Mgmt(vrfid=10, gw='172.16.31.254', gw2='172.16.31.251', dns='172.16.31.254')

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Call parent class to store the WSGI request and merge the class-level devices with the instance-level devices
        super().__init__(request, poc_id)

        # IP of Fabric-Studio is retrieved from the WSGI request: either from the VM selection or from a provided IP
        studio_ip = request.POST.get('vmIP') if request.POST.get('vmIP') else request.POST.get('vmInstance')
        if studio_ip == '0.0.0.0':  # fpoc-manager is running inside the Fabric-Studio
            self.manager_inside_studio = True
            self.ip = self.mgmt.gw  # device is accessed by fpoc-manager from within the Fabric-Studio OOB inside IP
        else:  # fpoc-manager is running outside the Fabric-Studio
            self.manager_inside_studio = False
            self.ip = studio_ip  # device is accessed by fpoc-manager via the Fabric-Studio outside IP

        # Configure default values for FortiGate VMs running inside a Fabric-Studio
        # model is KVM64, speed is 'auto' for all lan and wan interfaces, reboot_delay is 120 seconds
        for device in self.devices.values():
            if isinstance(device, FortiGate):
                device.model = "FGT_VM64_KVM"
                device.reboot_delay = 120
                if device.lan is not None:
                    device.lan.speed = 'auto'
                for intf_name, intf in device.wan:
                    if intf is not None:
                        intf.speed = 'auto'

    def members(self, devices: dict = None, devnames: list = None):
        """
        only keep some devices
        for each device which is kept: merge the class-level attributes with the instance-level attributes
        """
        # Call parent class to do the device filtering and the class-level/device-level attribute merge
        super().members(devices, devnames)

        # configure access attributes for each device (name, IP@, SSH/HTTPS ports) depending on whether it is accessed
        # from within the Fabric-Studio (direct) or from the Fabric-Studio public IP (external NAT)
        for key_name, device in self.devices.items():
            device.name_phy = device.name_phy or key_name   # init to 'key_name' if 'name_phy' is None
            device.name = device.name or device.name_phy  # init to 'name_phy' if 'name' is None
            if self.manager_inside_studio:  # fpoc-manager is running inside the Fabric-Studio
                # device is accessed via its mgmt-ip inside the Fabric-Studio OOB
                device.ip = device.mgmt.ip  # e.g. 172.16.31.1
                device.https_port = 443
                device.ssh_port = 22
            else:  # fpoc-manager is running outside the Fabric-Studio
                device.ip = self.ip  # device is accessed via the Fabric-Studio outside IP
                device.https_port = self.BASE_PORT_HTTPS + device.offset
                device.ssh_port = self.BASE_PORT_SSH + device.offset

    @classmethod
    @property
    def name(cls):
        """
        Return the name of the Class itself
        """
        return cls.__name__
