import typing

from fpoc import FortiLab, FortiGate, LXC, VyOS
from fpoc.PoC_VPN import StudioVPN
from fpoc.PoC_SDWAN import FabricStudioSDWAN, AgoraSDWAN

# Type Hint:

TypeDevice = typing.Union[FortiGate, LXC, VyOS]
TypePoC = typing.Union[FortiLab, StudioVPN, FabricStudioSDWAN, AgoraSDWAN]
