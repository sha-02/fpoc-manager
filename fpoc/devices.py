from dataclasses import dataclass
import ipaddress
from enum import Enum


class Interface:
    # port: str  # e.g. 'port1'
    # vlanid: int  # e.g, 11
    # _ipaddress: ipaddress

    def __init__(self, port:str, vlanid: int, address: str):
        self.port = port
        self.vlanid = vlanid

        if len(address.split('.')) == 3:  # address is a subnet of the form '198.51.100'
            # kept for backward compatibility with previous code
            self._ipaddress = ipaddress.ip_network(address+'.0/24')
        elif '/' in address:  # address is an IP@ or a subnet of the form '198.51.100.1/24'
            self._ipaddress = ipaddress.ip_interface(address)
        else:  # address is an IP@ of the form '198.51.100.1'
            self._ipaddress = ipaddress.ip_address(address)

    def __repr__(self):
        return f'{self.__class__.__name__}(port={self.port}, vlanid={self.vlanid}, address={self.ipmask})'

    @property
    def interface(self) -> str:  # alias for 'port'
        return self.port

    @property
    def subnet(self) -> str:  # e.g., '198.51.100' for subnet '198.51.100.0/24' (for compatibility with previous code)
        return '.'.join(self._ipaddress.network_address.compressed.split('.')[0:3])

    @property
    def subnetmask(self) -> str:
        return self._ipaddress.network.compressed  # e.g. '172.16.31.0/24'

    @property
    def ip(self) -> str:
        return self._ipaddress.ip.compressed  # e.g. '172.16.31.1'

    @property
    def ipmask(self) -> str:
        return self._ipaddress.with_prefixlen  # e.g. '172.16.31.1/24'


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

    def __iter__(self):
        """"
        Makes the class an iterable which can iterate over the WAN interfaces
        Leverage the iterator from the class '__dict__' iterable
        """
        return iter(self.__dict__.items())


@dataclass
class Device:
    offset: int = None  # Offset of this device in the FortiPoC (used for SSH/HTTPS mgmt port)

    ip: str = None  # IP@ used to access the device = IP@ of the FortiPoC or mgmt_ip of the device within FortiPoC
    ssh_port: int = None  # e.g., 10100+offset (access from FortiPoC IP) or 22 (access from within FortiPoC)
    https_port: int = None  # e.g., 10400+offset (access from FortiPoC IP) or 443 (access from within FortiPoC)

    mgmt: Interface = None  # (port, vlanid, ipaddress/mask) for the OOB mgmt inside the FortiPoC (eg, ('port10', 0, '172.16.31.1/24'))
    mgmt_fpoc_ipmask: str = None  # IP@ of the FortiPoC in the OOB mgmt subnet inside the FortiPoC (eg, '172.16.31.254/24')

    name: str = None  # Name of the device for the poc
    name_fpoc: str = None  # Name of the device in the FortiPoC
    username: str = None  # username for SSH session
    password: str = None  # password for SSH session

    wan: WAN = None  # hardcoded WAN subnets (underlays) defined in the FortiPoC

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
        """
        """
        return ipaddress.ip_interface(self.mgmt_fpoc_ipmask).ip.compressed  # e.g. '172.16.31.254' when mgmt_ipmask='172.16.31.254/24'


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
    apiadmin: str = None  # username for the API admin
    apikey: str = None  # API key for the API admin
    fos_version: str = None  # FortiOS version running on the FGT. For e.g., "6.0.13"
    fos_version_target: str = None  # FortiOS requested by the user. For e.g., "6.0.13"
    ha: FortiGate_HA = None  # Initializing default value here does not work well, so it is done in __post_init__

    def __post_init__(self):  # Apply default values
        super(FortiGate, self).__post_init__()  # Call parent __post_init__
        #
        # initialize attributes inherited from parent class
        self.username = self.username or 'admin'  # initialize if it is None
        self.password = self.password or 'fortinet'  # initialize if it is None
        self.template_filename = self.template_filename or '_FGT.conf'  # initialize if it is None
        self.template_context['name'] = self.name
        #
        # initialize attributes from local class
        self.apiadmin = 'adminapi'
        self.ha = FortiGate_HA(mode=FortiGate_HA.Modes.STANDALONE, role=FortiGate_HA.Roles.STANDALONE)

    @property
    def FOS(self):  # long integer of the fos_version, e.g. "6.0.13" returns 6_000_013 (used for django template)
        """
        """
        major, minor, patch = self.fos_version.split('.')
        return int(major) * 1_000_000 + int(minor) * 1_000 + int(patch)


@dataclass
class LXC(Device):
    def __post_init__(self):  # Apply default values
        super(LXC, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'root'  # initialize if it is None
        self.password = self.password or 'fortinet'  # initialize if it is None
        self.template_context.setdefault('name', self.name)  # initialize if key does not exist
        self.template_context.setdefault('interface', 'eth0')  # initialize if key does not exist
        self.template_context.setdefault('vlan', None)  # initialize if key does not exist


@dataclass
class Vyos(Device):
    def __post_init__(self):  # Apply default values
        super(Vyos, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'vyos'  # initialize if it is None
        self.password = self.password or 'vyos'  # initialize if it is None


@dataclass
class FortiManager(Device):
    def __post_init__(self):  # Apply default values
        super(FortiManager, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'admin'  # initialize if it is None
        self.password = self.password or 'fortinet'  # initialize if it is None
