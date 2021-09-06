from dataclasses import dataclass
import string

@dataclass
class WanSettings:
    port: str  # e.g. 'port1'
    vlanid: int  # e.g, 11
    subnet: str  # e.g., '198.51.100'


@dataclass
class WAN:
    inet: WanSettings
    inet_snat: WanSettings
    inet_dnat: WanSettings
    inet1: WanSettings
    inet1_snat: WanSettings
    inet1_dnat: WanSettings
    inet2: WanSettings
    inet2_snat: WanSettings
    inet2_dnat: WanSettings
    inet3: WanSettings
    inet3_snat: WanSettings
    inet3_dnat: WanSettings
    mpls1: WanSettings
    mpls2: WanSettings


@dataclass
class Device:
    ip: str = None  # IP@ of the FortiPoC VM inside which this Device is running
    ssh_port: int = None  # e.g., 10100 , used to SSH to the Device via the FortiPoC VM IP@
    https_port: int = None  # e.g., 10400 , used to HTTPS to the Device via the FortiPoC VM IP@

    mgmt_subnet: str = None # OOB management subnet inside the FortiPoC used to access the Devices
    mgmt_lastbyte: str = None  # last-byte of this Device in the OOB mgmt subnet

    name: str = None  # Name of the device
    username: str = None  # username for SSH session
    password: str = None  # password for SSH session

    wan: WAN = None  # hardcoded WAN subnets (underlays) defined in the FortiPoC

    output: str = None  # output for the SSH commands executed on the device
    template_context: dict = None  # Dictionary needed for the Django template to render the template configuration
    template_group: str = None  # name of the template group to which belongs this device
    template_filename: str = None # name of the file in the template group
    config: str = None  # configuration to be deployed to the device
    commands: list = None  # List of CLI commands to be executed on the device

    deployment_status: str = None # e.g. 'completed' or 'skipped'

    def __post_init__(self):  # Apply default values
        self.template_group = self.template_group or self.name  # initialize if it is None
        self.template_context = self.template_context or {}  # initialize if it is None

    @property
    def mgmt_ip(self):
        # IP@ of this Device in the OOB management subnet inside the FortiPoC used to access the Devices
        return self.mgmt_subnet + self.mgmt_lastbyte

    @property
    def mgmt_ip_fpoc(self):
        # IP@ of the FortiPoC in the OOB management subnet inside the FortiPoC used to access the Devices
        return self.mgmt_subnet + '254' # last-byte of FortiPoC in OOB management is .254


@dataclass
class FortiGate(Device):
    apiadmin: str = None  # username for the API admin
    apikey: str = None  # API key for the API admin
    fos_version: str = None  # FortiOS version running on the FGT. For e.g., "6.0.13"
    fos_version_target: str = None  # FortiOS requested by the user. For e.g., "6.0.13"

    @property
    def FOS(self):  # long integer of the fos_version, e.g. "6.0.13" returns 6_000_013 (used for django template)
        major, minor, patch = self.fos_version.split('.')
        return int(major)*1_000_000 + int(minor)*1_000 + int(patch)

    # @property
    # def FOS(self):  # hexadecimal integer of the fos_version, e.g. "6.0.13" returns 0x60D (used for django template)
    #     major, minor, patch = self.fos_version.split('.')
    #     return int(''.join([string.hexdigits[int(major)], string.hexdigits[int(minor)], string.hexdigits[int(patch)]]), 16)

    def __post_init__(self):  # Apply default values
        super(FortiGate, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'admin'  # initialize if it is None
        self.password = self.password or 'fortinet'  # initialize if it is None
        self.apiadmin = self.apiadmin or 'adminapi'  # initialize if it is None
        self.template_filename = self.template_filename or '_FGT.conf' # initialize if it is None
        # self.template_context.setdefault('name', self.name)  # initialize if key does not exist
        # self.template_context.setdefault('FOS', 600)  # initialize to FortiOS 6.0.0 if key does not exist


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
class Vyos(Device):  # Apply default values
    def __post_init__(self):
        super(Vyos, self).__post_init__()  # Call parent __post_init__
        self.username = self.username or 'vyos'  # initialize if it is None
        self.password = self.password or 'vyos'  # initialize if it is None
