from django.core.handlers.wsgi import WSGIRequest

from fpoc import FortiLab
from fpoc.devices import FortiGate


class FortiPoC(FortiLab):
    BASE_PORT_SSH = 11000  # SSH ports for FortiPoC devices are 11000 + poc-devid: 11001, 11002, 11003, ...
    BASE_PORT_HTTPS = 14000  # HTTPS ports for FortiPoC devices are 14000 + poc-devid: 14001, 14002, 14003, ...
    # mgmt_fpoc_ipmask = '172.16.31.254/24'  # mgmt IP@ of FortiPoC in its OOB management subnet
    mgmt_gw = '172.16.31.254'      # Gateway for OOB mgmt network (override FortiLab parent class attribute)
    mgmt_dns = '172.16.31.254'     # DNS from the OOB mgmt (override FortiLab parent class attribute)
    mgmt_vrf = 10                  # VRF for the OOB mgmt (override FortiLab parent class attribute)

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Call parent class to store the WSGI request and merge the class-level devices with the instance-level devices
        super(FortiPoC, self).__init__(request, poc_id)

        # IP of FortiPoC is retrieved from the WSGI request: either from the fpoc selection or from a provided IP
        fpoc_ip = request.POST.get('fpocIP') if request.POST.get('fpocIP') else request.POST.get('pocInstance')
        if fpoc_ip == '0.0.0.0':  # fpoc-manager is running inside the FortiPoC
            self.manager_inside_fpoc = True
            self.ip = self.mgmt_gw  # device is accessed by fpoc-manager from within the FortiPoC OOB inside IP
        else:  # fpoc-manager is running outside the FortiPoC
            self.manager_inside_fpoc = False
            self.ip = fpoc_ip  # device is accessed by fpoc-manager via the FortiPoC outside IP

        # Configure default values for FortiGate VMs running inside a FortiPoC
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
        super(FortiPoC, self).members(devices, devnames)

        # configure access attributes for each device (name, IP@, SSH/HTTPS ports) depending on whether it is accessed
        # from within the FortiPoC (direct) or from the FortiPoC public IP (external NAT)
        for fpoc_devname, device in self.devices.items():
            device.name_fpoc = fpoc_devname
            device.name = device.name or device.name_fpoc  # init to 'name_fpoc' if 'name' is None
            # device.mgmt_fpoc_ipmask = self.__class__.mgmt_fpoc_ipmask
            if self.manager_inside_fpoc:  # fpoc-manager is running inside the FortiPoC
                # device is accessed via its mgmt-ip inside the FortiPoC OOB
                device.ip = device.mgmt.ip  # e.g. 172.16.31.1
                device.https_port = 443
                device.ssh_port = 22
            else:  # fpoc-manager is running outside the FortiPoC
                device.ip = self.ip  # device is accessed via the FortiPoC outside IP
                device.https_port = self.BASE_PORT_HTTPS + device.offset
                device.ssh_port = self.BASE_PORT_SSH + device.offset

    @classmethod
    @property
    def name(cls):
        """
        Return the name of the Class itself
        """
        return cls.__name__


class FabricStudio(FortiPoC):
    # BASE_PORT_HTTPS = 13000  # default HTTPS ports for FabricStudio devices (13000 + devid): 13000, 13001, 13002, ...

    # Fabric Studio has a reverse proxy which blocks API call on the default HTTPS redirection ports (13000 + devid)
    # So I configured additional HTTPS redirections with a base port of 20000
    BASE_PORT_HTTPS = 20000
