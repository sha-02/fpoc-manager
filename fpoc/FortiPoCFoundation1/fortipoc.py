from django.core.handlers.wsgi import WSGIRequest
import copy
import threading

from fpoc import FortiPoC, FortiGate, LXC, Vyos, FortiManager, WAN, Interface


class FortiPoCFoundation1(FortiPoC):
    """
    """
    devices = {
        'FGT-A': FortiGate(offset=0, mgmt=Interface('port10', 0, '172.16.31.11/24'),
                           wan=WAN(
                               inet=Interface('port1', 0, '198.51.100'),
                               inet1=Interface('port1', 11, '100.64.11'),
                               inet2=Interface('port1', 12, '100.64.12'),
                               inet3=Interface('port1', 13, '100.64.13'),
                               inet_snat=Interface('port1', 200, '192.168.200'),
                               inet_dnat=Interface('port1', 201, '192.168.201'),
                               inet1_snat=Interface('port1', 210, '192.168.210'),
                               inet1_dnat=Interface('port1', 211, '192.168.211'),
                               inet2_snat=Interface('port1', 220, '192.168.220'),
                               inet2_dnat=Interface('port1', 221, '192.168.221'),
                               inet3_snat=Interface('port1', 230, '192.168.230'),
                               inet3_dnat=Interface('port1', 231, '192.168.231'),
                               mpls1=Interface('port2', 14, '10.0.14'), mpls2=Interface('port2', 15, '10.0.15'))),

        'FGT-A_sec': FortiGate(offset=1, mgmt=Interface('port10', 0, '172.16.31.12/24'),
                               wan=WAN(
                                   inet=Interface('port1', 0, '198.51.100'),
                                   inet1=Interface('port1', 211, '100.64.211'),
                                   inet2=Interface('port1', 212, '100.64.212'),
                                   inet3=Interface('port1', 213, '100.64.213'),
                                   inet_snat=Interface('port1', 200, '192.168.200'),
                                   inet_dnat=Interface('port1', 201, '192.168.201'),
                                   inet1_snat=Interface('port1', 210, '192.168.210'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211'),
                                   inet2_snat=Interface('port1', 220, '192.168.220'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221'),
                                   inet3_snat=Interface('port1', 230, '192.168.230'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231'),
                                   mpls1=Interface('port2', 214, '10.0.214'),
                                   mpls2=Interface('port2', 215, '10.0.215'))),

        'FGT-B': FortiGate(offset=2, mgmt=Interface('port10', 0, '172.16.31.21/24'),
                           wan=WAN(
                               inet=Interface('port1', 0, '203.0.113'),
                               inet1=Interface('port1', 21, '100.64.21'),
                               inet2=Interface('port1', 22, '100.64.22'),
                               inet3=Interface('port1', 23, '100.64.23'),
                               inet_snat=Interface('port1', 200, '192.168.200'),
                               inet_dnat=Interface('port1', 201, '192.168.201'),
                               inet1_snat=Interface('port1', 210, '192.168.210'),
                               inet1_dnat=Interface('port1', 211, '192.168.211'),
                               inet2_snat=Interface('port1', 220, '192.168.220'),
                               inet2_dnat=Interface('port1', 221, '192.168.221'),
                               inet3_snat=Interface('port1', 230, '192.168.230'),
                               inet3_dnat=Interface('port1', 231, '192.168.231'),
                               mpls1=Interface('port2', 24, '10.0.24'), mpls2=Interface('port2', 25, '10.0.25'))),

        'FGT-B_sec': FortiGate(offset=3, mgmt=Interface('port10', 0, '172.16.31.22/24'),
                               wan=WAN(
                                   inet=Interface('port1', 0, '203.0.113'),
                                   inet1=Interface('port1', 221, '100.64.221'),
                                   inet2=Interface('port1', 222, '100.64.222'),
                                   inet3=Interface('port1', 223, '100.64.223'),
                                   inet_snat=Interface('port1', 200, '192.168.200'),
                                   inet_dnat=Interface('port1', 201, '192.168.201'),
                                   inet1_snat=Interface('port1', 210, '192.168.210'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211'),
                                   inet2_snat=Interface('port1', 220, '192.168.220'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221'),
                                   inet3_snat=Interface('port1', 230, '192.168.230'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231'),
                                   mpls1=Interface('port2', 224, '10.0.224'),
                                   mpls2=Interface('port2', 225, '10.0.225'))),

        'FGT-C': FortiGate(offset=4, mgmt=Interface('port10', 0, '172.16.31.31/24'),
                           wan=WAN(
                               inet=Interface('port1', 0, '192.0.2'),
                               inet1=Interface('port1', 31, '100.64.31'),
                               inet2=Interface('port1', 32, '100.64.32'),
                               inet3=Interface('port1', 33, '100.64.33'),
                               inet_snat=Interface('port1', 200, '192.168.200'),
                               inet_dnat=Interface('port1', 201, '192.168.201'),
                               inet1_snat=Interface('port1', 210, '192.168.210'),
                               inet1_dnat=Interface('port1', 211, '192.168.211'),
                               inet2_snat=Interface('port1', 220, '192.168.220'),
                               inet2_dnat=Interface('port1', 221, '192.168.221'),
                               inet3_snat=Interface('port1', 230, '192.168.230'),
                               inet3_dnat=Interface('port1', 231, '192.168.231'),
                               mpls1=Interface('port2', 34, '10.0.34'), mpls2=Interface('port2', 35, '10.0.35'))),

        'FGT-C_sec': FortiGate(offset=5, mgmt=Interface('port10', 0, '172.16.31.32/24'),
                               wan=WAN(
                                   inet=Interface('port1', 0, '192.0.2'),
                                   inet1=Interface('port1', 231, '100.64.231'),
                                   inet2=Interface('port1', 232, '100.64.232'),
                                   inet3=Interface('port1', 233, '100.64.233'),
                                   inet_snat=Interface('port1', 200, '192.168.200'),
                                   inet_dnat=Interface('port1', 201, '192.168.201'),
                                   inet1_snat=Interface('port1', 210, '192.168.210'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211'),
                                   inet2_snat=Interface('port1', 220, '192.168.220'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221'),
                                   inet3_snat=Interface('port1', 230, '192.168.230'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231'),
                                   mpls1=Interface('port2', 234, '10.0.234'),
                                   mpls2=Interface('port2', 235, '10.0.235'))),

        'FGT-D': FortiGate(offset=6, mgmt=Interface('port10', 0, '172.16.31.41/24'),
                           wan=WAN(
                               inet=Interface('port1', 0, '100.64.40'),
                               inet1=Interface('port1', 41, '100.64.41'),
                               inet2=Interface('port1', 42, '100.64.42'),
                               inet3=Interface('port1', 43, '100.64.43'),
                               inet_snat=Interface('port1', 200, '192.168.200'),
                               inet_dnat=Interface('port1', 201, '192.168.201'),
                               inet1_snat=Interface('port1', 210, '192.168.210'),
                               inet1_dnat=Interface('port1', 211, '192.168.211'),
                               inet2_snat=Interface('port1', 220, '192.168.220'),
                               inet2_dnat=Interface('port1', 221, '192.168.221'),
                               inet3_snat=Interface('port1', 230, '192.168.230'),
                               inet3_dnat=Interface('port1', 231, '192.168.231'),
                               mpls1=Interface('port2', 44, '10.0.44'), mpls2=Interface('port2', 45, '10.0.45'))),

        'FGT-D_sec': FortiGate(offset=7, mgmt=Interface('port10', 0, '172.16.31.42/24'),
                               wan=WAN(
                                   inet=Interface('port1', 0, '100.64.40'),
                                   inet1=Interface('port1', 241, '100.64.241'),
                                   inet2=Interface('port1', 242, '100.64.242'),
                                   inet3=Interface('port1', 243, '100.64.243'),
                                   inet_snat=Interface('port1', 200, '192.168.200'),
                                   inet_dnat=Interface('port1', 201, '192.168.201'),
                                   inet1_snat=Interface('port1', 210, '192.168.210'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211'),
                                   inet2_snat=Interface('port1', 220, '192.168.220'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221'),
                                   inet3_snat=Interface('port1', 230, '192.168.230'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231'),
                                   mpls1=Interface('port2', 244, '10.0.244'),
                                   mpls2=Interface('port2', 245, '10.0.245'))),

        'ISFW-A': FortiGate(offset=8, mgmt=Interface('port10', 0, '172.16.31.13/24')),
        'Internet': Vyos(offset=9, mgmt=Interface('eth9', 0, '172.16.31.251/24')),
        'MPLS': Vyos(offset=10, mgmt=Interface('eth9', 0, '172.16.31.252/24')),
        'PC_A1': LXC(offset=11, mgmt=Interface('eth9', 0, '172.16.31.111/24')),
        'PC_A2': LXC(offset=12, mgmt=Interface('eth9', 0, '172.16.31.112/24')),
        'PC_B1': LXC(offset=13, mgmt=Interface('eth9', 0, '172.16.31.121/24')),
        'PC_B2': LXC(offset=14, mgmt=Interface('eth9', 0, '172.16.31.122/24')),
        'PC_C1': LXC(offset=15, mgmt=Interface('eth9', 0, '172.16.31.131/24')),
        'PC_C2': LXC(offset=16, mgmt=Interface('eth9', 0, '172.16.31.132/24')),
        'PC_D1': LXC(offset=17, mgmt=Interface('eth9', 0, '172.16.31.141/24')),
        'PC_D2': LXC(offset=18, mgmt=Interface('eth9', 0, '172.16.31.142/24')),
        'RTR-NAT_A': LXC(offset=19, mgmt=Interface('eth9', 0, '172.16.31.10/24')),
        'RTR-NAT_B': LXC(offset=20, mgmt=Interface('eth9', 0, '172.16.31.20/24')),
        'RTR-NAT_C': LXC(offset=21, mgmt=Interface('eth9', 0, '172.16.31.30/24')),
        'RTR-NAT_D': LXC(offset=22, mgmt=Interface('eth9', 0, '172.16.31.40/24')),
        'SRV_INET': LXC(offset=23, mgmt=Interface('eth9', 0, '172.16.31.100/24')),
        'WAN_Controller': LXC(offset=24, mgmt=Interface('eth9', 0, '172.16.31.250/24')),
        'FMG': FortiManager(offset=25, mgmt=Interface('port1', 0, '172.16.31.200/24')),
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0, devices: dict = None, fpoc_devnames: list = None):
        """
        Build a poc for some devices
        'devices' or 'fpoc_devnames' provides the list of devices to keep (filter) out of the class 'devices'
        The devices to be kept/filtered can be provided in two ways:
        - via 'devices': dict of devices of the form {'fpoc_devname': FortiGate(...), 'fpoc_devname': LXC(...), ...}
        - via 'fpoc_devnames': list of device names

        Each device name (in list 'fpoc_devnames' or the keys in 'devices' dict) must correspond to a key in
        FOUNDATION1.devices dictionary.
        """

        # The poc instance self.devices dict can be built from 'devices' or from 'fpoc_devname'
        # One of them must be passed as argument, not both
        if devices and fpoc_devnames:
            raise TypeError("'devices' and 'fpoc_devnames' cannot be both provided")

        # Initialize this poc instance
        self.id = poc_id
        self.lock = threading.Lock()  # mutual exclusion (mutex) lock used for concurrency (e.g., download FOS firmware)

        # IP of FortiPoC is retrieved from the fpoc selection list or from an IP provided by user
        fpoc_ip = request.POST.get('fpocIP') if request.POST.get('fpocIP') else request.POST.get('fpocSelection')
        if fpoc_ip == '0.0.0.0':  # fpoc-manager is running inside the FortiPoC
            self.manager_inside_fpoc = True
            self.ip = '172.16.31.254'  # device is accessed by fpoc-manager via the FortiPoC OOB inside IP
        else:  # fpoc-manager is running outside the FortiPoC
            self.manager_inside_fpoc = False
            self.ip = fpoc_ip  # device is accessed by fpoc-manager via the FortiPoC outside IP

        #
        # build the dict of all devices needed for this poc: self.devices
        #

        # If no specific device filter is requested then the list of devices for this instance
        # (self.devices) is inherited from its class and contain all devices.
        if devices is None and fpoc_devnames is None:
            pass  # Nothing to do, self.devices is FOUNDATION1.devices

        elif fpoc_devnames:  # Build the poc self.devices dict from the list of fpoc device name in 'fpoc_devnames'
            self.devices = { fpoc_devname: FortiPoCFoundation1.devices[fpoc_devname] for fpoc_devname in fpoc_devnames }

        elif devices:  # Build the poc self.devices dict from the 'devices' dict
            self.devices = {}
            # "merge" the attributes from a device defined in the Class with its counter-part passed as argument
            for fpoc_devname, device in devices.items():
                # Retrieve all the device's attributes from the Class
                self.devices[fpoc_devname] = copy.copy(FortiPoCFoundation1.devices[fpoc_devname])  # Shallow copy is Ok
                # Update (or Override) with all attributes from the device passed as argument
                for k, v in device.__dict__.items():
                    if v is not None:
                        self.devices[fpoc_devname].__dict__[k] = v

        # Now that the list of devices is built (either from class or from filter), configure some attributes for
        # each device (IP@, SSH/HTTPS ports)
        for fpoc_devname, device in self.devices.items():
            device.name_fpoc = fpoc_devname
            device.name = device.name or device.name_fpoc  # init to 'name_fpoc' if 'name' is None
            device.mgmt_fpoc_ipmask = FortiPoCFoundation1.mgmt_fpoc_ipmask
            if self.manager_inside_fpoc:  # fpoc-manager is running inside the FortiPoC
                # device is accessed via its mgmt-ip inside the FortiPoC OOB
                device.ip = device.mgmt.ip  # e.g. 172.16.31.1
                device.https_port = 443
                device.ssh_port = 22
            else:  # fpoc-manager is running outside the FortiPoC
                device.ip = fpoc_ip  # device is accessed via the FortiPoC outside IP
                device.https_port = FortiPoCFoundation1.BASE_PORT_HTTPS + device.offset
                device.ssh_port = FortiPoCFoundation1.BASE_PORT_SSH + device.offset

    def devices_of_type(*args) -> dict:
        """
        Returns a dict of devices of the same type (e.g., 'FortiGate' or 'LXC' or 'Vyos')
        The 'type' is passed as a mandatory positional argument (at 1st or 2nd position depending on the kind of call)
        Can be called as an instance method or as a class method
        Call as a class method:
            FortiPoCFoundation1.devices_of_type(FortiGate)  => args == (FortiGate)
        Call as an instance method:
            FortiPoCFoundation1().devices_of_type(FortiGate) => args == (<object-instance>, FortiGate)
        """
        if (not args  # called as a class method without device type
                or isinstance(args[0], FortiPoCFoundation1) and len(args) == 1):  # called as an instance method without device type
            raise TypeError('Invalid number of arguments, a device type must be provided')

        if isinstance(args[0], FortiPoCFoundation1):  # called as an instance method
            self, type_ = args
        else:  # called as a class method
            self = FortiPoCFoundation1
            type_ = args[0]

        return {k: v for k, v in self.devices.items() if isinstance(v, type_)}
