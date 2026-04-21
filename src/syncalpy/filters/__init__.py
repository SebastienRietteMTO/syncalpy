"""Filter module."""

from .future_only import FutureOnlyFilter
from .regexp import RegexpSummaryFilter, RegexpDescriptionFilter, RegexpLocationFilter

FILTER_REGISTRY = {
    "future_only": FutureOnlyFilter,
    "regexp_summary": RegexpSummaryFilter,
    "regexp_description": RegexpDescriptionFilter,
    "regexp_location": RegexpLocationFilter,
}


def get_filter(filter_name: str, **params):
    """Get filter instance by name."""
    filter_class = FILTER_REGISTRY.get(filter_name)
    if not filter_class:
        raise ValueError(f"Unknown filter: {filter_name}")
    return filter_class(**params)


__all__ = ["FutureOnlyFilter", "RegexpSummaryFilter", "RegexpDescriptionFilter", "RegexpLocationFilter", "get_filter", "FILTER_REGISTRY"]
