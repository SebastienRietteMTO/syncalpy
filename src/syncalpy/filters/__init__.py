"""Filter module."""

from .future_only import FutureOnlyFilter
from .regexp import RegexpFilter

FILTER_REGISTRY = {
    "future_only": FutureOnlyFilter,
    "regexp": RegexpFilter,
}


def get_filter(filter_name: str, **params):
    """Get filter instance by name."""
    filter_class = FILTER_REGISTRY.get(filter_name)
    if not filter_class:
        raise ValueError(f"Unknown filter: {filter_name}")
    return filter_class(**params)


__all__ = ["FutureOnlyFilter", "RegexpFilter", "get_filter", "FILTER_REGISTRY"]
