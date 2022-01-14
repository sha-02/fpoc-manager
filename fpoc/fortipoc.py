from django.core.handlers.wsgi import WSGIRequest
import typing
import copy
import threading

from fpoc.devices import FortiGate, LXC, Vyos
from fpoc.devices import WAN, WanSettings

# Type Hint:
TypeDevice = typing.TypeVar("TypeDevice", FortiGate, LXC, Vyos)


class FortiPoC:
    BASE_PORT_SSH = 10100  # SSH ports for FortiPoC devices are 10100 + poc-devid: 10101, 10102, 10103, ...
    BASE_PORT_HTTPS = 10400  # HTTPS ports for FortiPoC devices are 10400 + poc-devid: 10401, 10402, 10403, ...
    mgmt_fpoc_ipmask = '172.16.31.254/24'  # mgmt IP@ of FortiPoC in its OOB management subnet
    manager_inside_fpoc = True
    ip = '172.16.31.254'  # IP@ used by fpoc-manager to access the FortiPoC VM
    # it is the mgmt_fpoc IP@ when the fpoc-manager runs inside the FortiPoC VM
    devices: dict
    # Dict[DeviceHint]

    def __iter__(self):
        # Makes the class an iterable which can iterate over the devices stored in the 'devices' dictionary
        # Leverage the iterator from 'devices' iterable
        return iter(self.devices.values())

    @classmethod
    @property
    def name(cls):  # Return the name of the Class itself
        """
        """
        return cls.__name__


class FortiPoCFoundation1(FortiPoC):
    """
    """
    lock: threading.Lock  # mutual exclusion (mutex) lock used to download and store missing firmware
    devices = {
        'FGT-A': FortiGate(offset=0, mgmt_ipmask='172.16.31.1/24',
                           wan=WAN(
                               inet=WanSettings('port1', 0, '198.51.100'),
                               inet1=WanSettings('port1', 11, '100.64.11'),
                               inet2=WanSettings('port1', 12, '100.64.12'),
                               inet3=WanSettings('port1', 13, '100.64.13'),
                               inet_snat=WanSettings('port1', 200, '192.168.200'),
                               inet_dnat=WanSettings('port1', 201, '192.168.201'),
                               inet1_snat=WanSettings('port1', 210, '192.168.210'),
                               inet1_dnat=WanSettings('port1', 211, '192.168.211'),
                               inet2_snat=WanSettings('port1', 220, '192.168.220'),
                               inet2_dnat=WanSettings('port1', 221, '192.168.221'),
                               inet3_snat=WanSettings('port1', 230, '192.168.230'),
                               inet3_dnat=WanSettings('port1', 231, '192.168.231'),
                               mpls1=WanSettings('port2', 14, '10.0.14'), mpls2=WanSettings('port2', 15, '10.0.15'))),

        'FGT-A_sec': FortiGate(offset=1, mgmt_ipmask='172.16.31.13/24',
                               wan=WAN(
                                   inet=WanSettings('port1', 0, '198.51.100'),
                                   inet1=WanSettings('port1', 11, '100.64.11'),
                                   inet2=WanSettings('port1', 12, '100.64.12'),
                                   inet3=WanSettings('port1', 13, '100.64.13'),
                                   inet_snat=WanSettings('port1', 200, '192.168.200'),
                                   inet_dnat=WanSettings('port1', 201, '192.168.201'),
                                   inet1_snat=WanSettings('port1', 210, '192.168.210'),
                                   inet1_dnat=WanSettings('port1', 211, '192.168.211'),
                                   inet2_snat=WanSettings('port1', 220, '192.168.220'),
                                   inet2_dnat=WanSettings('port1', 221, '192.168.221'),
                                   inet3_snat=WanSettings('port1', 230, '192.168.230'),
                                   inet3_dnat=WanSettings('port1', 231, '192.168.231'),
                                   mpls1=WanSettings('port2', 14, '10.0.14'),
                                   mpls2=WanSettings('port2', 15, '10.0.15'))),

        'FGT-B': FortiGate(offset=2, mgmt_ipmask='172.16.31.2/24',
                           wan=WAN(
                               inet=WanSettings('port1', 0, '203.0.113'),
                               inet1=WanSettings('port1', 21, '100.64.21'),
                               inet2=WanSettings('port1', 22, '100.64.22'),
                               inet3=WanSettings('port1', 23, '100.64.23'),
                               inet_snat=WanSettings('port1', 200, '192.168.200'),
                               inet_dnat=WanSettings('port1', 201, '192.168.201'),
                               inet1_snat=WanSettings('port1', 210, '192.168.210'),
                               inet1_dnat=WanSettings('port1', 211, '192.168.211'),
                               inet2_snat=WanSettings('port1', 220, '192.168.220'),
                               inet2_dnat=WanSettings('port1', 221, '192.168.221'),
                               inet3_snat=WanSettings('port1', 230, '192.168.230'),
                               inet3_dnat=WanSettings('port1', 231, '192.168.231'),
                               mpls1=WanSettings('port2', 24, '10.0.24'), mpls2=WanSettings('port2', 25, '10.0.25'))),

        'FGT-B_sec': FortiGate(offset=3, mgmt_ipmask='172.16.31.14/24',
                               wan=WAN(
                                   inet=WanSettings('port1', 0, '203.0.113'),
                                   inet1=WanSettings('port1', 21, '100.64.21'),
                                   inet2=WanSettings('port1', 22, '100.64.22'),
                                   inet3=WanSettings('port1', 23, '100.64.23'),
                                   inet_snat=WanSettings('port1', 200, '192.168.200'),
                                   inet_dnat=WanSettings('port1', 201, '192.168.201'),
                                   inet1_snat=WanSettings('port1', 210, '192.168.210'),
                                   inet1_dnat=WanSettings('port1', 211, '192.168.211'),
                                   inet2_snat=WanSettings('port1', 220, '192.168.220'),
                                   inet2_dnat=WanSettings('port1', 221, '192.168.221'),
                                   inet3_snat=WanSettings('port1', 230, '192.168.230'),
                                   inet3_dnat=WanSettings('port1', 231, '192.168.231'),
                                   mpls1=WanSettings('port2', 24, '10.0.24'),
                                   mpls2=WanSettings('port2', 25, '10.0.25'))),

        'FGT-C': FortiGate(offset=4, mgmt_ipmask='172.16.31.9/24',
                           wan=WAN(
                               inet=WanSettings('port1', 0, '192.0.2'),
                               inet1=WanSettings('port1', 31, '100.64.31'),
                               inet2=WanSettings('port1', 32, '100.64.32'),
                               inet3=WanSettings('port1', 33, '100.64.33'),
                               inet_snat=WanSettings('port1', 200, '192.168.200'),
                               inet_dnat=WanSettings('port1', 201, '192.168.201'),
                               inet1_snat=WanSettings('port1', 210, '192.168.210'),
                               inet1_dnat=WanSettings('port1', 211, '192.168.211'),
                               inet2_snat=WanSettings('port1', 220, '192.168.220'),
                               inet2_dnat=WanSettings('port1', 221, '192.168.221'),
                               inet3_snat=WanSettings('port1', 230, '192.168.230'),
                               inet3_dnat=WanSettings('port1', 231, '192.168.231'),
                               mpls1=WanSettings('port2', 34, '10.0.34'), mpls2=WanSettings('port2', 35, '10.0.35'))),

        'FGT-C_sec': FortiGate(offset=5, mgmt_ipmask='172.16.31.15/24',
                               wan=WAN(
                                   inet=WanSettings('port1', 0, '192.0.2'),
                                   inet1=WanSettings('port1', 31, '100.64.31'),
                                   inet2=WanSettings('port1', 32, '100.64.32'),
                                   inet3=WanSettings('port1', 33, '100.64.33'),
                                   inet_snat=WanSettings('port1', 200, '192.168.200'),
                                   inet_dnat=WanSettings('port1', 201, '192.168.201'),
                                   inet1_snat=WanSettings('port1', 210, '192.168.210'),
                                   inet1_dnat=WanSettings('port1', 211, '192.168.211'),
                                   inet2_snat=WanSettings('port1', 220, '192.168.220'),
                                   inet2_dnat=WanSettings('port1', 221, '192.168.221'),
                                   inet3_snat=WanSettings('port1', 230, '192.168.230'),
                                   inet3_dnat=WanSettings('port1', 231, '192.168.231'),
                                   mpls1=WanSettings('port2', 34, '10.0.34'),
                                   mpls2=WanSettings('port2', 35, '10.0.35'))),

        'FGT-D': FortiGate(offset=6, mgmt_ipmask='172.16.31.22/24',
                           wan=WAN(
                               inet=WanSettings('port1', 0, '100.64.40'),
                               inet1=WanSettings('port1', 41, '100.64.41'),
                               inet2=WanSettings('port1', 42, '100.64.42'),
                               inet3=WanSettings('port1', 43, '100.64.43'),
                               inet_snat=WanSettings('port1', 200, '192.168.200'),
                               inet_dnat=WanSettings('port1', 201, '192.168.201'),
                               inet1_snat=WanSettings('port1', 210, '192.168.210'),
                               inet1_dnat=WanSettings('port1', 211, '192.168.211'),
                               inet2_snat=WanSettings('port1', 220, '192.168.220'),
                               inet2_dnat=WanSettings('port1', 221, '192.168.221'),
                               inet3_snat=WanSettings('port1', 230, '192.168.230'),
                               inet3_dnat=WanSettings('port1', 231, '192.168.231'),
                               mpls1=WanSettings('port2', 44, '10.0.44'), mpls2=WanSettings('port2', 45, '10.0.45'))),

        'FGT-D_sec': FortiGate(offset=7, mgmt_ipmask='172.16.31.23/24',
                               wan=WAN(
                                   inet=WanSettings('port1', 0, '100.64.40'),
                                   inet1=WanSettings('port1', 41, '100.64.41'),
                                   inet2=WanSettings('port1', 42, '100.64.42'),
                                   inet3=WanSettings('port1', 43, '100.64.43'),
                                   inet_snat=WanSettings('port1', 200, '192.168.200'),
                                   inet_dnat=WanSettings('port1', 201, '192.168.201'),
                                   inet1_snat=WanSettings('port1', 210, '192.168.210'),
                                   inet1_dnat=WanSettings('port1', 211, '192.168.211'),
                                   inet2_snat=WanSettings('port1', 220, '192.168.220'),
                                   inet2_dnat=WanSettings('port1', 221, '192.168.221'),
                                   inet3_snat=WanSettings('port1', 230, '192.168.230'),
                                   inet3_dnat=WanSettings('port1', 231, '192.168.231'),
                                   mpls1=WanSettings('port2', 44, '10.0.44'),
                                   mpls2=WanSettings('port2', 45, '10.0.45'))),

        'ISFW-A': FortiGate(offset=8, mgmt_ipmask='172.16.31.19/24'),
        'Internet': Vyos(offset=9, mgmt_ipmask='172.16.31.251/24'),
        'MPLS': Vyos(offset=10, mgmt_ipmask='172.16.31.252/24'),
        'PC_A1': LXC(offset=11, mgmt_ipmask='172.16.31.3/24'),
        'PC_A2': LXC(offset=12, mgmt_ipmask='172.16.31.5/24'),
        'PC_B1': LXC(offset=13, mgmt_ipmask='172.16.31.4/24'),
        'PC_B2': LXC(offset=14, mgmt_ipmask='172.16.31.6/24'),
        'PC_C1': LXC(offset=15, mgmt_ipmask='172.16.31.10/24'),
        'PC_C2': LXC(offset=16, mgmt_ipmask='172.16.31.11/24'),
        'PC_D1': LXC(offset=17, mgmt_ipmask='172.16.31.16/24'),
        'PC_D2': LXC(offset=18, mgmt_ipmask='172.16.31.17/24'),
        'RTR-NAT_A': LXC(offset=19, mgmt_ipmask='172.16.31.7/24'),
        'RTR-NAT_B': LXC(offset=20, mgmt_ipmask='172.16.31.8/24'),
        'RTR-NAT_C': LXC(offset=21, mgmt_ipmask='172.16.31.12/24'),
        'RTR-NAT_D': LXC(offset=22, mgmt_ipmask='172.16.31.18/24'),
        'SRV_INET': LXC(offset=23, mgmt_ipmask='172.16.31.20/24'),
    }

    def __init__(self, request: WSGIRequest, poc_id: int, devices: dict):
        # Initialize this particular PoC instance/object
        self.id = poc_id
        self.devices = {}
        self.lock = threading.Lock()

        # "merge" the attributes from a device defined in the Class with its counter-part passed as argument
        for fpoc_devname, device in devices.items():
            # Retrieve all underlay WAN info from the Class device
            self.devices[fpoc_devname] = copy.copy(FortiPoCFoundation1.devices[fpoc_devname])  # Shallow copy is Ok
            # Retrieve all attributes from the device passed as argument
            for k, v in device.__dict__.items():
                if v is not None:
                    self.devices[fpoc_devname].__dict__[k] = v

            self.devices[fpoc_devname].name_fpoc = fpoc_devname

        # mgmt attributes of each device (IP@, SSH/HTTPS ports)
        for device in self.devices.values():
            device.mgmt_fpoc_ipmask = FortiPoCFoundation1.mgmt_fpoc_ipmask
            # IP of FortiPoC is retrieved from the fpoc selection list or from an IP provided by user
            ip = request.POST.get('fpocIP') if request.POST.get('fpocIP') else request.POST.get('fpocSelection')
            if ip == '0.0.0.0':  # fpoc-manager is running inside the FortiPoC
                # self.ip and self.manager_inside_fpoc values are inherited from the Class
                # device is accessed via its mgmt-ip inside the FortiPoC
                device.ip = device.mgmt_ip  # e.g. 172.16.31.1
                device.https_port = 443
                device.ssh_port = 22
            else:  # fpoc-manager is running outside the FortiPoC
                self.manager_inside_fpoc = False
                device.ip = self.ip = ip  # device is accessed via the FortiPoC IP
                device.https_port = FortiPoCFoundation1.BASE_PORT_HTTPS + device.offset
                device.ssh_port = FortiPoCFoundation1.BASE_PORT_SSH + device.offset


# Type Hint:
TypePoC = typing.TypeVar("TypePoC", FortiPoC, FortiPoCFoundation1)
