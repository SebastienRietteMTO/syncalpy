"""Calendar model."""

from dataclasses import dataclass, field
from typing import List, Optional
from .event import CalendarEvent


@dataclass
class Calendar:
    """Represents a calendar with events."""

    name: str
    events: List[CalendarEvent] = field(default_factory=list)
    url: str = ""
    protocol: str = ""
    username: str = ""
    password: str = ""
    filters: List[str] = field(default_factory=list)

    def get_event_by_uid(self, uid: str) -> Optional[CalendarEvent]:
        """Get an event by its UID."""
        for event in self.events:
            if event.uid == uid:
                return event
        return None

    def add_event(self, event: CalendarEvent) -> None:
        """Add an event to the calendar."""
        existing = self.get_event_by_uid(event.uid)
        if existing:
            self.events.remove(existing)
        self.events.append(event)

    def remove_event(self, uid: str) -> bool:
        """Remove an event by UID. Returns True if removed."""
        event = self.get_event_by_uid(uid)
        if event:
            self.events.remove(event)
            return True
        return False

    def diff(self, other: "Calendar") -> dict:
        """Compare this calendar with another.

        Returns dict with:
        - added: events in self but not in other (new events in self)
        - removed: events in other but not in self (deleted from self)
        - modified: events in both but different
        """
        self_uids = {e.uid for e in self.events}
        other_uids = {e.uid for e in other.events}

        added = [e for e in self.events if e.uid not in other_uids]
        removed = [e for e in other.events if e.uid not in self_uids]

        modified = []
        for self_event in self.events:
            if self_event.uid in other_uids:
                other_event = other.get_event_by_uid(self_event.uid)
                if other_event and not self.events_equal(self_event, other_event):
                    modified.append((self_event, other_event))

        return {
            "added": added,
            "removed": removed,
            "modified": modified,
        }

    @staticmethod
    def events_equal(e1: CalendarEvent, e2: CalendarEvent) -> bool:
        """Check if two events have the same content."""
        return (
            e1.summary == e2.summary
            and e1.start == e2.start
            and e1.end == e2.end
            and (e1.description or "") == (e2.description or "")
            and (e1.location or "") == (e2.location or "")
        )
