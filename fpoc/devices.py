from dataclasses import dataclass
import ipaddress
from enum import Enum


class Interface:
    # port: str  # e.g. 'port1'
    # vlanid: int  # e.g, 11
    # _address: ipaddress

    def __init__(self, port:str, vlanid: int, address: str):
        self.port = port
        self.vlanid = vlanid

        if len(address.split('.')) == 3:  # address is a network of the form '198.51.100'
            # kept for backward compatibility with previous code
            self._address = ipaddress.ip_interface(address + '.0/24')
        elif '/' in address:  # address is an IP@ or a subnet of the form '198.51.100.0/24' or '198.51.100.1/24'
            self._address = ipaddress.ip_interface(address)

    def __repr__(self):
        return f'{self.__class__.__name__}(port={self.port}, vlanid={self.vlanid}, address={str(self._address)})'

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
        return self._address.with_prefixlen  # e.g. '172.16.31.1/24'

    def dictify(self):
        """
        Make a dictionary out of this Object
        This is needed for FMG CLI script template
        """
        return {
            'port': self.port,
            'interface': self.port,
            'vlanid': self.vlanid,
            'subnet': self.subnet,
            'subnetmask': self.network,
            'ip': self.ip,
            'ipmask': self.ipmask
        }


class Network:
    def __init__(self, network: str):
        self.network = network

    def __repr__(self):
        return f'{self.network}'

    def dictify(self):
        return self.__dict__


@dataclass
class WAN:
    inet: Interface
    inet_snat: Interface
    inet_dnat: Interface
    inet1: Interface
    inet1_snat: Interface
    inet1_dnat: Interface
    inet2: Interface
    inet2_snat: Interface
    inet2_dnat: Interface
    inet3: Interface
    inet3_snat: Interface
    inet3_dnat: Interface
    mpls1: Interface
    mpls2: Interface
    mpls_summary: Network = None    # Summary for MPLS underlay (e.g. '10.71.0.0/16')

    def __iter__(self):
        """"
        Makes the class an iterable which can iterate over the WAN interfaces
        Leverage the iterator from the class '__dict__' iterable
        """
        return iter(self.__dict__.items())

    def dictify(self):
        """
        Make a dictionary out of this Object
        This is needed for FMG CLI script template
        """
        return { wan_name: interface.dictify() for wan_name, interface in self }


@dataclass
class Device:
    offset: int = None  # Offset of this device if inside a FortiPoC (used to derive SSH/HTTPS external port)

    ip: str = None  # IP@ used to access the device (eg, direct IP or external.NAT/fortipoc IP)
    ssh_port: int = 22  # direct access (22) or from external NAT (eg, FortiPoC 10100+offset)
    https_port: int = 443  # direct access (443) or from external NAT (eg, FortiPoC 10400+offset)

    mgmt: Interface = None  # mgmt settings (port, vlanid, ipaddress/mask): for eg ('port10', 0, '172.16.31.1/24')
    mgmt_fpoc_ipmask: str = None  # IP@ of the FortiPoC in the mgmt subnet inside FortiPoC (eg, '172.16.31.254/24')

    name: str = None  # Name configured on the device
    name_fpoc: str = None  # Name of the device in the FortiPoC
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

    @property
    def mgmt_fpoc_ip(self):
        # e.g. '172.16.31.254' when mgmt_ipmask='172.16.31.254/24'
        return ipaddress.ip_interface(self.mgmt_fpoc_ipmask).ip.compressed


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
    model: str = "FGT_VM64_KVM"   # FGT model as displayed in the firmware filename
    apiv2auth: bool = True  # True= Use APIv2 authentication based on admin/password ; False= Use API admin
    apiadmin: str = 'adminapi'  # username for the API admin
    apikey: str = None  # API key for the API admin
    fos_version: str = None  # FortiOS version running on the FGT. For e.g., "6.0.13"
    fos_version_target: str = None  # FortiOS requested by the user. For e.g., "6.0.13"
    ha: FortiGate_HA = None  # Initializing default value here does not work well, so it is done in __post_init__
    lan: Interface = None  # used to define the LAN connectivity (eg, "port5")
    wan: WAN = None  # hardcoded WAN subnets (underlays) defined in the FortiPoC

    def __post_init__(self):  # Apply default values
        super(FortiGate, self).__post_init__()  # Call parent __post_init__
        #
        # initialize attributes inherited from parent class
        self.username = self.username or 'admin'  # initialize if it is None
        self.password = self.password or 'nsefortinet'  # initialize if it is None
        self.template_filename = self.template_filename or '_FGT.conf'  # initialize if it is None
        self.template_context['name'] = self.name
        #
        # initialize attributes from local class
        # self.apiadmin = 'adminapi'
        self.ha = FortiGate_HA(mode=FortiGate_HA.Modes.STANDALONE, role=FortiGate_HA.Roles.STANDALONE)

    @classmethod
    def FOS_int(cls, fos_version: str):
        # converts a FOS version string "6.0.13" to a long integer 6_000_013
        major, minor, patch = fos_version.split('.')
        return int(major) * 1_000_000 + int(minor) * 1_000 + int(patch)

    @property
    def FOS(self):
        # long integer of the fos_version, e.g. 6_000_013 for 6.0.13, used in django templates to compare FOS versions
        return self.__class__.FOS_int(self.fos_version)


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


@dataclass
class VyOS(Device):
    def __post_init__(self):  # Apply default values
        super(VyOS, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'vyos'  # initialize if it is None
        self.password = self.password or 'vyos'  # initialize if it is None
        self.template_filename = self.template_filename or 'vyos.conf'  # initialize if it is None


@dataclass
class FortiManager(Device):
    def __post_init__(self):  # Apply default values
        super(FortiManager, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'admin'  # initialize if it is None
        self.password = self.password or 'nsefortinet'  # initialize if it is None
