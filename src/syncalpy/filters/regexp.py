"""Regexp filters - matches events by regex pattern on specific fields."""

import re
from typing import List
from ..event import CalendarEvent


class RegexpSummaryFilter:
    """Filter events by regex pattern on summary."""

    def __init__(self, pattern: str):
        """Initialize filter.

        Args:
            pattern: Regular expression pattern to match.
        """
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def filter(self, events: List[CalendarEvent]) -> List[CalendarEvent]:
        """Filter events matching the pattern."""
        return [e for e in events if self.pattern.search(e.summary)]


class RegexpDescriptionFilter:
    """Filter events by regex pattern on description."""

    def __init__(self, pattern: str):
        """Initialize filter.

        Args:
            pattern: Regular expression pattern to match.
        """
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def filter(self, events: List[CalendarEvent]) -> List[CalendarEvent]:
        """Filter events matching the pattern."""
        return [e for e in events if e.description and self.pattern.search(e.description)]


class RegexpLocationFilter:
    """Filter events by regex pattern on location."""

    def __init__(self, pattern: str):
        """Initialize filter.

        Args:
            pattern: Regular expression pattern to match.
        """
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def filter(self, events: List[CalendarEvent]) -> List[CalendarEvent]:
        """Filter events matching the pattern."""
        return [e for e in events if e.location and self.pattern.search(e.location)]
