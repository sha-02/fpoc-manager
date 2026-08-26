from __future__ import annotations  # Allows to reference a class as a type hint during the declaration of the class itself

import copy
from dataclasses import dataclass
import ipaddress
from enum import Enum
from typing import Callable
from fpoc.exceptions import StopProcessingDevice


class Interface:
    # port: str  # e.g. 'port1'
    # vlanid: int  # e.g, 11
    # _address: ipaddress
    def __init__(self, port:str|None = None, vlanid: int|None = None, address: str|None = None, name: str|None = None, speed: str|None = None,
                 vrfid: int|None = None, alias: str|None = None):
        # All parameters must default to None due to the update() method used by FortiGate class
        self.port = port
        self.vlanid = vlanid
        self.vrfid = vrfid
        self.speed = speed
        self.dhcp = None    # must default to None because of the update() method
        self._address = None

        self._name = name if vlanid else port
            # for VLAN interface: '_name' is the name of the VLAN interface and 'port' is the parent interface
            # for non-VLAN interface: '_name' and 'port' both reference the physical interface

        if alias is None and vlanid is not None and name is not None:
            # a name and a vlanid [0-x] was specified: use this name also as an alias
            self.alias = name
        else:
            self.alias = alias

        if address is None:
            self._address = ipaddress.ip_interface('1.2.3.4/32')
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
                f'address={"dhcp" if self.dhcp else (self._address)}, name={self.name}, speed={self.speed}, '
                f'alias={self.alias})')

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


# @dataclass
# class WAN:
#     # All attributes must default to None due to the update() method used by FortiGate class
#     inet: Interface|None = None
#     inet_snat: Interface|None = None
#     inet_dnat: Interface|None = None
#     inet1: Interface|None = None
#     inet1_snat: Interface|None = None
#     inet1_dnat: Interface|None = None
#     inet2: Interface|None = None
#     inet2_snat: Interface|None = None
#     inet2_dnat: Interface|None = None
#     inet3: Interface|None = None
#     inet3_snat: Interface|None = None
#     inet3_dnat: Interface|None = None
#     mpls1: Interface|None = None
#     mpls2: Interface|None = None
#     mpls_summary: Network|None = None    # Summary for MPLS underlay (e.g. '10.71.0.0/16')
#
#     def __iter__(self):
#         """"
#         Makes the class an iterable which can iterate over the WAN interfaces
#         Leverage the iterator from the class '__dict__' iterable
#         """
#         return iter(self.__dict__.items())
#
#     def update(self, wan: WAN):
#         # Update (Override) this WAN instance with all not-None attributes from the 'wan' passed as argument
#         for k, v in wan:  # 'self' is iterable due to redefinition of __iter__()
#             if v is not None and k is not None and isinstance(self.__dict__[k], Interface):
#                 self.__dict__[k].update(v)    # update Interface 'k' with Interface 'v'
#             else:
#                 self.__dict__[k] = v
#
#     # def dictify(self):
#     #     """
#     #     Make a dictionary out of this Object
#     #     This is needed for FMG CLI script template
#     #     """
#     #     return { wan_name: interface.dictify() for wan_name, interface in self }


class WAN:
    """
    Container for dynamically named WAN interfaces.

    Interfaces are stored internally in a dictionary but can be accessed
    using normal attribute syntax.

    Example:
        wan = WAN(inet=IFACE("eth0"), mpls1=IFACE("port5"))

        wan.inet
        wan.mpls1
        wan.inet2 = IFACE("eth1")

        wan = WAN(
            inet=IFACE("eth0"),
            mpls1=IFACE("port5"),
        )

        # Attribute-style access
        print(wan.inet)
        print(wan.mpls1)

        # Add dynamically
        wan.inet2 = IFACE("eth1")

        # Iterate over name/interface pairs
        for name, iface in wan.items():
            print(name, iface)

        # Iterate over names
        for name in wan:
            print(name)

        # Iterate over interfaces
        for iface in wan.values():
            print(iface)

        # Dictionary-like operations
        if "inet" in wan:
            print(wan.inet)

        print(len(wan))
    """
    mpls_summary: Network | None = None  # Summary for MPLS underlay (e.g. '10.71.0.0/16')

    def __init__(self, **ifaces):
        # Store all interfaces in a private dictionary.
        if 'mpls_summary' in ifaces.keys():
            object.__setattr__(self,'mpls_summary', ifaces['mpls_summary'])
            del(ifaces['mpls_summary'])

        object.__setattr__(self, "_ifaces", dict(ifaces))

    def __getattr__(self, name):
        """
        Called when normal attribute lookup fails.

        For example:
            wan.inet

        becomes:
            wan._ifaces["inet"]
        """
        if name == "_ifaces":
            raise AttributeError(name)

        ifaces = object.__getattribute__(self, "_ifaces")

        try:
            return ifaces[name]
        except KeyError:
            raise AttributeError(
                f"{type(self).__name__} has no attribute {name!r}"
            ) from None

    def __setattr__(self, name, value):
        """
        Store dynamically assigned attributes in the internal dictionary.

        For example:
            wan.inet = IFACE("eth0")

        becomes:
            wan._ifaces["inet"] = IFACE("eth0")
        """
        if name == 'mpls_summary':
            object.__setattr__(self, 'mpls_summary', value)
        else:
            self._ifaces[name] = value

    def __iter__(self):
        """
        Iterate over (name, interface) pairs.

        This allows:
            for name, iface in wan.items():
                ...
        """
        return iter(self._ifaces.items())

    def items(self):
        """
        Iterate over (name, interface) pairs.

        This allows:
            for name, iface in wan.items():
                ...
        """
        return self._ifaces.items()

    def keys(self):
        """Return an iterable of interface names."""
        return self._ifaces.keys()

    def values(self):
        """Return an iterable of interfaces."""
        return self._ifaces.values()

    def __len__(self):
        """Return the number of interfaces."""
        return len(self._ifaces)

    def __contains__(self, name):
        """Allow: 'inet' in wan"""
        return name in self._ifaces

    def update(self, wan: WAN):
        # Update (Override) this WAN instance with all not-None attributes from the 'wan' passed as argument
        for k, v in wan.items():
            if v is None:
                self._ifaces[k] = None
            elif k in self._ifaces:
                self._ifaces[k].update(v)   # update Interface 'k' with Interface 'v'
            else:
                self._ifaces[k] = copy.deepcopy(v)  # add Interface 'v'


@dataclass
class Device:
    # All attributes must default to None due to the update() method used by FortiGate class
    offset: int|None = None  # Offset of this device if inside Fabric-Studio (used to derive SSH/HTTPS external port)
    nameid: str|None = None  # name used by Fabric-Studio for the console access

    ip: str|None = None  # IP@ used to access the device (eg, direct IP or external.NAT/studio IP)
    ssh_port: int|None = None  # direct access (22) or from external NAT (eg, Fabric-Studio 10100+offset)
    https_port: int|None = None  # direct access (443) or from external NAT (eg, Fabric-Studio 10400+offset)

    reboot_delay: int|None = None     # number of seconds to wait for the device to perform a full reboot

    mgmt: Interface|None = None  # OOB mgmt settings (port, vlanid, ipaddress/mask): for eg ('port10', 0, '172.16.31.1/24')

    name: str|None = None  # Name configured on the device
    name_phy: str|None = None  # "Physical" Name of the device in the Fabric-Studio or in the Hardware Lab
    username: str|None = None  # username for SSH session
    password: str|None = None  # password for SSH session

    output: str|None = None  # output for the SSH commands executed on the device
    template_context: dict|None = None  # Dictionary needed for the Django template to render the template configuration
    template_group: str|None = None  # name of the template group to which belongs this device
    template_filename: str|None = None  # name of the file in the template group (e.g. '_FGT.conf')
    config: str|None = None  # configuration to be deployed to the device
    commands: list|None = None  # List of CLI commands to be executed on the device

    deployment_status: str|None = None  # e.g. 'completed' or 'skipped'

    _callback: Callable|None = None  # Callback function which can be registered to the class instance and can be called later on

    def __post_init__(self):  # Apply default values
        # self.template_group = self.template_group or self.name  # initialize if it is None
        self.template_context = self.template_context or {}  # initialize if it is None

    def callback_register(self, callback_func: Callable):
        """
        Register a callback function which can be called later on
        """
        self._callback = callback_func

    def callback(self):
        """
        Call the callback function passing the class instance (self) as an argument
        In case the callback is supposed to return something, then return the result of this call
        """
        return self._callback(self) if self._callback else None


@dataclass
class FortiGate_HA:
    class Modes(Enum):
        STANDALONE = 0
        FGCP = 1
        FGSP = 2        # Not yet implemented
        FGCP_FGSP = 3   # Not yet implemented

    class Roles(Enum):
        STANDALONE = 0
        PRIMARY = 1
        SECONDARY = 2

    mode: Modes = Modes.FGCP  # HA mode from Enum Modes
    role: Roles = Roles.PRIMARY  # HA role from Enum Roles
    group_id: int|None = None
    group_name: str|None = None
    hbdev: list|None = None  # list of HA heartbeat interfaces with their priorities (e.g. [('port6', 0), ('port7', 0)])
    sessyncdev: list|None = None  # list of HA session synch devices (e.g. ['port6', 'port7'])
    monitordev: list|None = None  # list of HA monitored interfaces (e.g., ['port1', 'port2',  'port5'])
    priority: int|None = None  # HA priority
    mgmt_interfaces: bool|None = None

    def update(self, ha: FortiGate_HA):
        # Update (Override) this HA attributes with all not-None attributes from the 'ha' passed as argument
        if ha is None:
            return

        if self.mode == ha.mode and self.mode == self.__class__.Modes.FGCP:
            # 'ha' and 'self' are both FGCP
            for k, v in ha.__dict__.items():
                if v is not None:
                    self.__dict__[k] = v  # update 'self' with 'ha'
                    # when 'ha' attribute is None, 'self' keeps its current value for this attribute
            return

        self.__dict__ = ha.__dict__


@dataclass
class FortiGate(Device):
    alias: str|None = None   # alias name
    model: str|None = None # FGT model as displayed in the firmware filename
    npu: str|None = None     # NPU model for appliances

    fos_version: str|None = None  # FortiOS version running on the FGT. For e.g., "6.0.13"
    fos_version_target: str|None = None  # FortiOS requested by the user. For e.g., "6.0.13"

    lan: Interface|None = None  # used to define the LAN connectivity (eg, "port5")
    wan: WAN|None = None  # WAN underlays
    HA: FortiGate_HA|None = None  # Initializing default value here does not work well, so it is done in __post_init__

    apiv2auth: bool = False  # True= Use APIv2 authentication based on admin/password ; False= Use API admin
                             # APIv2 auth with admin/pwd is no longer supported as of 7.6.4, so I'm reverting to the API admin method
    apiadmin: str = 'adminapi'  # username for the API admin
    apikey: str = ''  # API key for the API admin

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
        # self.HA = self.HA or FortiGate_HA(mode=FortiGate_HA.Modes.STANDALONE, role=FortiGate_HA.Roles.STANDALONE)

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
        # Also returns an independent instance (deepcopy())
        for k, v in fortigate.__dict__.items():
            if v is None:
                continue
            if k == 'lan':
                if self.lan is None:
                    self.lan = fortigate.lan
                else:
                    self.lan.update(fortigate.lan)
            elif k == 'wan':
                if self.wan is None:
                    self.wan = fortigate.wan
                else:
                    self.wan.update(fortigate.wan)
            elif k == 'HA':
                if self.HA is None:
                    self.HA = fortigate.HA
                else:
                    self.HA.update(fortigate.HA)
            else:
                self.__dict__[k] = v  # update the local FortiGate attribute with the 'fortigate' attribute

        return copy.deepcopy(self)  # return an independent instance

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

    def update(self, vyos: VyOS):
        # Update (Override) this LXC instance with all not-None attributes from the 'vyos' passed as argument
        for k, v in vyos.__dict__.items():
            if v is not None:
                self.__dict__[k] = v    # update VyOS 'k' with VyOS 'v'
