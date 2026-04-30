"""Future only filter - keeps only events in the future."""

from datetime import datetime
from typing import List
from ..event import CalendarEvent


class FutureOnlyFilter:
    """Filter to keep only future events."""

    def __init__(self, reference_time: datetime = None):
        """Initialize filter.

        Args:
            reference_time: Time to compare against. Defaults to now.
        """
        self.reference_time = reference_time or datetime.now()

    def filter(self, events: List[CalendarEvent]) -> List[CalendarEvent]:
        """Filter events to keep only future ones."""
        result = []
        for event in events:
            start = event.DTSTART
            if start and start > self.reference_time:
                result.append(event)
            elif start is None:
                result.append(event)
        return result
