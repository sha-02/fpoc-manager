from __future__ import annotations  # Allows to reference a class as a type hint during the declaration of the class itself
from dataclasses import dataclass
import ipaddress
from enum import Enum
from fpoc.exceptions import StopProcessingDevice


class Interface:
    # port: str  # e.g. 'port1'
    # vlanid: int  # e.g, 11
    # _address: ipaddress

    def __init__(self, port:str = None, vlanid: int = None, address: str = None, name: str = None, speed: str = None,
                 vrfid: int = None, alias: str = None):
        # All parameters must default to None due to the update() method used by FortiGate class
        self.port = port
        self.vlanid = vlanid
        self.vrfid = vrfid
        self.speed = speed
        self.alias = alias
        self.dhcp = None    # must default to None because of the update() method

        self._name = name if vlanid else port
            # for VLAN interface: '_name' is the name of the VLAN interface and 'port' is the parent interface
            # for non-VLAN interface: '_name' and 'port' both reference the physical interface

        if address is None:
            self._address = None
        elif address == 'dhcp':
            self.dhcp = True
            self._address = ipaddress.ip_interface('1.2.3.4/32')
        elif len(address.split('.')) == 3:  # address is a network of the form '198.51.100'
            # kept for backward compatibility with previous code
            self._address = ipaddress.ip_interface(address + '.0/24')
            self.dhcp = False
        elif '/' in address:  # address is an IP@ or a subnet of the form '198.51.100.0/24' or '198.51.100.1/24'
            self._address = ipaddress.ip_interface(address)
            self.dhcp = False

    def __repr__(self):
        return (f'{self.__class__.__name__}(port={self.port}, vrfid={self.vrfid}, vlanid={self.vlanid}, '
                f'address={str(self._address)}, name={self.name}, speed={self.speed}, alias={self.alias})')

    @property
    def name(self) -> str:  # vlan name or physical interface name
        return self._name

    @property
    def interface(self) -> str:  # alias for 'port'
        return self.port

    @property
    def network(self) -> str:
        return str(self._address.network)  # e.g. '172.16.31.0/24'

    @property
    def subnet(self) -> str:  # e.g., '198.51.100' for subnet '198.51.100.0/24' (for compatibility with previous code)
        return '.'.join(self.network.split('.')[0:3])

    @property
    def ip(self) -> str:
        return str(self._address.ip)  # e.g. '172.16.31.1'

    @property
    def ipmask(self) -> str:
        return self._address.with_netmask.replace('/', ' ')  # e.g. '172.16.31.1 255.255.255.0'

    @property
    def ipprefix(self) -> str:
        return self._address.with_prefixlen  # e.g. '172.16.31.1/24'

    @property
    def mask(self) -> str:
        return str(self._address.netmask)  # e.g. '255.255.255.0'

    def update(self, interface: Interface):
        # Update (Override) this Interface instance with all not-None attributes from the 'interface' passed as argument
        for k, v in interface.__dict__.items():
            if v is not None:
                self.__dict__[k] = v    # update Interface 'k' with Interface 'v'

    # def dictify(self):
    #     """
    #     Make a dictionary out of this Object
    #     This is needed for FMG CLI script template
    #     """
    #     return {
    #         'port': self.port,
    #         'interface': self.port,
    #         'vlanid': self.vlanid,
    #         'subnet': self.subnet,
    #         'subnetmask': self.network,
    #         'ip': self.ip,
    #         'ipmask': self.ipmask
    #     }


class Network:
    def __init__(self, network: str):
        self.network = network

    def __repr__(self):
        return f'{self.network}'

    def dictify(self):
        return self.__dict__


@dataclass
class WAN:
    # All attributes must default to None due to the update() method used by FortiGate class
    inet: Interface = None
    inet_snat: Interface = None
    inet_dnat: Interface = None
    inet1: Interface = None
    inet1_snat: Interface = None
    inet1_dnat: Interface = None
    inet2: Interface = None
    inet2_snat: Interface = None
    inet2_dnat: Interface = None
    inet3: Interface = None
    inet3_snat: Interface = None
    inet3_dnat: Interface = None
    mpls1: Interface = None
    mpls2: Interface = None
    mpls_summary: Network = None    # Summary for MPLS underlay (e.g. '10.71.0.0/16')

    def __iter__(self):
        """"
        Makes the class an iterable which can iterate over the WAN interfaces
        Leverage the iterator from the class '__dict__' iterable
        """
        return iter(self.__dict__.items())

    def update(self, wan: WAN):
        # Update (Override) this WAN instance with all not-None attributes from the 'wan' passed as argument
        for k, v in wan:  # 'self' is iterable due to redefinition of __iter__()
            if v is not None and k is not None and isinstance(self.__dict__[k], Interface):
                self.__dict__[k].update(v)    # update Interface 'k' with Interface 'v'
            else:
                self.__dict__[k] = v

    # def dictify(self):
    #     """
    #     Make a dictionary out of this Object
    #     This is needed for FMG CLI script template
    #     """
    #     return { wan_name: interface.dictify() for wan_name, interface in self }


@dataclass
class Device:
    # All attributes must default to None due to the update() method used by FortiGate class
    offset: int = None  # Offset of this device if inside a FortiPoC (used to derive SSH/HTTPS external port)

    ip: str = None  # IP@ used to access the device (eg, direct IP or external.NAT/fortipoc IP)
    ssh_port: int = None  # direct access (22) or from external NAT (eg, FortiPoC 10100+offset)
    https_port: int = None  # direct access (443) or from external NAT (eg, FortiPoC 10400+offset)

    reboot_delay: int = None     # number of seconds to wait for the device to perform a full reboot

    mgmt: Interface = None  # OOB mgmt settings (port, vlanid, ipaddress/mask): for eg ('port10', 0, '172.16.31.1/24')
    # mgmt_fpoc_ipmask: str = None  # IP@ of the FortiPoC in the mgmt subnet inside FortiPoC (eg, '172.16.31.254/24')

    name: str = None  # Name configured on the device
    name_fpoc: str = None  # Name of the device in the FortiPoC or name of the device in the hardware Lab
    username: str = None  # username for SSH session
    password: str = None  # password for SSH session

    output: str = None  # output for the SSH commands executed on the device
    template_context: dict = None  # Dictionary needed for the Django template to render the template configuration
    template_group: str = None  # name of the template group to which belongs this device
    template_filename: str = None  # name of the file in the template group (e.g. '_FGT.conf')
    config: str = None  # configuration to be deployed to the device
    commands: list = None  # List of CLI commands to be executed on the device

    deployment_status: str = None  # e.g. 'completed' or 'skipped'

    def __post_init__(self):  # Apply default values
        self.template_group = self.template_group or self.name  # initialize if it is None
        self.template_context = self.template_context or {}  # initialize if it is None

    # @property
    # def mgmt_fpoc_ip(self):
    #     # e.g. '172.16.31.254' when mgmt_ipmask='172.16.31.254/24'
    #     return ipaddress.ip_interface(self.mgmt_fpoc_ipmask).ip.compressed

    # def update(self, device: Device):
    #     # Update (Override) this device instance with all not-None attributes from the 'device' passed as argument
    #     for k, v in device.__dict__.items():
    #         if v is not None:
    #             if k == 'reboot_delay':  # for reboot_delay, keep the biggest value of the two devices
    #                 self.reboot_delay = max(self.reboot_delay, v)
    #             else:
    #                 self.__dict__[k] = v    # update the local instance attribute with the 'device' attribute


@dataclass
class FortiGate_HA:
    class Modes(Enum):
        STANDALONE = 0
        FGCP = 1
        FGSP = 2
        FGCP_FGSP = 3

    class Roles(Enum):
        STANDALONE = 0
        PRIMARY = 1
        SECONDARY = 2

    mode: Modes = Modes.FGCP  # HA mode from Enum Modes
    role: Roles = Roles.PRIMARY  # HA role from Enum Roles
    group_id: int = None
    group_name: str = None
    hbdev: list = None  # list of HA heartbeat interfaces with their priorities (e.g. [('port6', 0), ('port7', 0)])
    sessyncdev: list = None  # list of HA session synch devices (e.g. ['port6', 'port7'])
    monitordev: list = None  # list of HA monitored interfaces (e.g., ['port1', 'port2',  'port5'])
    priority: int = None  # HA priority


@dataclass
class FortiGate(Device):
    alias: str = None   # alias name
    model: str = None # FGT model as displayed in the firmware filename
    npu: str = None     # NPU model for appliances

    fos_version: str = None  # FortiOS version running on the FGT. For e.g., "6.0.13"
    fos_version_target: str = None  # FortiOS requested by the user. For e.g., "6.0.13"

    lan: Interface = None  # used to define the LAN connectivity (eg, "port5")
    wan: WAN = None  # hardcoded WAN subnets (underlays) defined in the FortiPoC
    HA: FortiGate_HA = None  # Initializing default value here does not work well, so it is done in __post_init__

    apiv2auth: bool = True  # True= Use APIv2 authentication based on admin/password ; False= Use API admin
    apiadmin: str = 'adminapi'  # username for the API admin
    apikey: str = None  # API key for the API admin

    def __post_init__(self):  # Apply default values
        super(FortiGate, self).__post_init__()  # Call parent __post_init__
        #
        # initialize attributes inherited from parent class
        self.username = self.username or 'admin'  # initialize if it is None
        # self.password = self.password or 'nsefortinet'  # initialize if it is None
        self.template_filename = self.template_filename or '_FGT.conf'  # initialize if it is None
        self.template_context['name'] = self.name
        #
        # initialize attributes from local class
        # self.apiadmin = 'adminapi'
        self.HA = FortiGate_HA(mode=FortiGate_HA.Modes.STANDALONE, role=FortiGate_HA.Roles.STANDALONE)

    @classmethod
    def FOS_int(cls, fos_version: str):
        # converts a FOS version string "6.0.13" to a long integer 6_000_013
        major, minor, patch = fos_version.split('.')
        return int(major) * 1_000_000 + int(minor) * 1_000 + int(patch)

    @property
    def FOS(self):
        # long integer of the fos_version, e.g. 6_000_013 for 6.0.13, used in django templates to compare FOS versions
        return self.__class__.FOS_int(self.fos_version)

    def update(self, fortigate: FortiGate):
        # Update (Override) this FortiGate instance with not-None attributes from another FortiGate passed as argument
        for k, v in fortigate.__dict__.items():
            if v is None:
                continue
            if k == 'lan':
                if self.lan is not None:
                    self.lan.update(fortigate.lan)
                else:
                    self.lan = fortigate.lan
            elif k == 'wan' and self.wan is not None:
                if self.wan is not None:
                    self.wan.update(fortigate.wan)
                else:
                    self.wan = fortigate.wan
            else:
                self.__dict__[k] = v  # update the local FortiGate attribute with the 'fortigate' attribute


@dataclass
class LXC(Device):
    def __post_init__(self):  # Apply default values
        super(LXC, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'root'  # initialize if it is None
        self.password = self.password or 'nsefortinet'  # initialize if it is None
        self.template_filename = self.template_filename or 'lxc.conf'  # initialize if it is None
        self.template_context.setdefault('name', self.name)  # initialize if key does not exist
        self.template_context.setdefault('interface', 'eth0')  # initialize if key does not exist
        self.template_context.setdefault('vlan', None)  # initialize if key does not exist

    def update(self, lxc: LXC):
        # Update (Override) this LXC instance with all not-None attributes from the 'lxc' passed as argument
        for k, v in lxc.__dict__.items():
            if v is not None:
                self.__dict__[k] = v    # update LXC 'k' with LXC 'v'


@dataclass
class VyOS(Device):
    def __post_init__(self):  # Apply default values
        super(VyOS, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'vyos'  # initialize if it is None
        self.password = self.password or 'vyos'  # initialize if it is None
        self.template_filename = self.template_filename or 'vyos.conf'  # initialize if it is None
