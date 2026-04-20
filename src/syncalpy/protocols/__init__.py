"""Protocol module."""

from .caldav import CalDAVProtocol
from .ics_file import ICSFileProtocol
from .zimbra import ZimbraProtocol

PROTOCOL_REGISTRY = {
    "caldav": CalDAVProtocol,
    "ics_file": ICSFileProtocol,
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
    "ZimbraProtocol",
    "get_protocol",
    "PROTOCOL_REGISTRY",
]
