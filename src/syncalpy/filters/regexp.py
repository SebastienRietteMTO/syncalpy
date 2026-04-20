"""Regexp filter - matches events by regex pattern."""

import re
from typing import List
from ..event import CalendarEvent


class RegexpFilter:
    """Filter events by regex pattern on title or description."""

    def __init__(self, pattern: str, field: str = "any"):
        """Initialize filter.

        Args:
            pattern: Regular expression pattern to match.
            field: Which field to match ('title', 'description', 'any').
        """
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.field = field

    def filter(self, events: List[CalendarEvent]) -> List[CalendarEvent]:
        """Filter events matching the pattern."""
        result = []
        for event in events:
            if self._matches(event):
                result.append(event)
        return result

    def _matches(self, event: CalendarEvent) -> bool:
        """Check if event matches the pattern."""
        if self.field in ("title", "any"):
            if self.pattern.search(event.summary):
                return True

        if self.field in ("description", "any"):
            if event.description and self.pattern.search(event.description):
                return True

        return False
