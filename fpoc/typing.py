import typing

from fpoc import FortiLab, FortiPoC, FortiGate, LXC, VyOS
from fpoc.FortiPoCFoundation1 import FortiPoCFoundation1
from fpoc.FortiPoCSDWAN import FortiPoCSDWAN, FortiLabSDWAN

# Type Hint:

TypeDevice = typing.Union[FortiGate, LXC, VyOS]
TypePoC = typing.Union[FortiLab, FortiPoC, FortiPoCFoundation1, FortiPoCSDWAN, FortiLabSDWAN]
