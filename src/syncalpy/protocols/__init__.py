"""Protocol module."""

from .caldav import CalDAVProtocol
from .ics_file import ICSFileProtocol
from .jcal import JCalProtocol
from .zimbra import ZimbraProtocol

PROTOCOL_REGISTRY = {
    "caldav": CalDAVProtocol,
    "ics_file": ICSFileProtocol,
    "jcal": JCalProtocol,
    "zimbra": ZimbraProtocol,
}


def get_protocol(protocol_name: str):
    """Get protocol class by name."""
    protocol_class = PROTOCOL_REGISTRY.get(protocol_name)
    if not protocol_class:
        raise ValueError(f"Unknown protocol: {protocol_name}")
    return protocol_class


__all__ = [
    "CalDAVProtocol",
    "ICSFileProtocol",
    "JCalProtocol",
    "ZimbraProtocol",
    "get_protocol",
    "PROTOCOL_REGISTRY",
]
