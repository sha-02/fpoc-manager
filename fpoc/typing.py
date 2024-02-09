import typing

from fpoc import FortiPoC, FortiGate, LXC, VyOS, FortiManager
from fpoc.FortiPoCFoundation1 import FortiPoCFoundation1
from fpoc.FortiPoCSDWAN import FortiPoCSDWAN

# Type Hint:
# TypeDevice = typing.TypeVar("TypeDevice", FortiGate, LXC, VyOS, FortiManager)
# TypePoC = typing.TypeVar("TypePoC", FortiPoC, FortiPoCFoundation1, FortiPoCSDWAN)

TypeDevice = typing.Union[FortiGate, LXC, VyOS, FortiManager]
TypePoC = typing.Union[FortiPoC, FortiPoCFoundation1, FortiPoCSDWAN]
