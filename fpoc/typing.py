import typing

from fpoc import FortiPoC, FortiGate, LXC, Vyos, FortiManager
from fpoc.FortiPoCFoundation1 import FortiPoCFoundation1

# Type Hint:
TypeDevice = typing.TypeVar("TypeDevice", FortiGate, LXC, Vyos, FortiManager)
TypePoC = typing.TypeVar("TypePoC", FortiPoC, FortiPoCFoundation1)
