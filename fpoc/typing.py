from typing import Union

from fpoc.fortilab import FortiLab
from fpoc.devices import FortiGate, LXC, VyOS
from fpoc.PoC_VPN import StudioVPN
from fpoc.PoC_SDWAN.fabric_studio import FabricStudioSDWAN
from fpoc.PoC_SDWAN.agora import AgoraSDWAN

# Type Hint:

TypeDevice = Union[FortiGate, LXC, VyOS]
TypePoC = Union[FortiLab, StudioVPN, FabricStudioSDWAN, AgoraSDWAN]
