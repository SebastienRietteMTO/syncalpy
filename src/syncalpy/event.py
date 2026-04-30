"""Event model for calendar events."""

from typing import Optional
import uuid
import re
from icalendar import Event, Calendar


class CalendarEvent(Event):
    """Represents a calendar event."""

    ignore_keys_eq = {"CREATED", "LAST-MODIFIED", "DTSTAMP"}

    def __init__(self, **kwargs):
        """Initialize CalendarEvent."""
        super().__init__()
        self._hidden = False

    @property
    def is_hidden(self) -> bool:
        """Check if the event is hidden."""
        return self._hidden

    def hide(self) -> None:
        """Hide the event."""
        self._hidden = True

    def set_uid(self, uid: str = None) -> None:
        """Set the event UID, generating a new one if not provided."""
        if uid is None:
            uid = uuid.uuid4().hex
        self.uid = uid

    def to_ical(self) -> str:
        """Convert event to ICS format using icalendar's to_ical()."""
        return super().to_ical().decode('utf-8')

    @staticmethod
    def create(properties=None, vevent=None):
        """Factory method to create CalendarEvent from a dictionary or VEVENT string."""
        if properties and vevent:
            raise ValueError("Cannot pass both properties and vevent")

        if vevent:
            try:
                cal = Calendar.from_ical(vevent)
                components = cal.walk()
                if not components:
                    return None
                event = CalendarEvent()
                event.update(components[0])
                return event
            except Exception:
                return None

        if properties:
            event = CalendarEvent()
            hidden = properties.pop("_hidden", None)
            properties = {k: v for k, v in properties.items() if v}
            event.update(Event.new(**properties))
            if hidden is not None:
                event._hidden = hidden
            return event

    def __eq__(self, other):
        """Compare events excluding CREATED, LAST-MODIFIED, and DTSTAMP."""
        if not isinstance(other, CalendarEvent):
            return False
        self_keys = {k for k in self.keys() if k not in self.ignore_keys_eq}
        other_keys = {k for k in other.keys() if k not in self.ignore_keys_eq}
        if self_keys != other_keys:
            return False
        return all(self.get(k) == other.get(k) for k in self_keys)

    def conflict(self) -> None:
        """Mark this event as a conflict by prefixing summary with [CONFLICT]."""
        pattern = r"^\[CONFLICT(\s+(\d+))?\]\s*"
        match = re.match(pattern, self.summary)

        if not match:
            self.summary = f"[CONFLICT] {self.summary}"
        else:
            num_str = match.group(2)
            if num_str is None:
                self.summary = re.sub(pattern, "[CONFLICT 2] ", self.summary, count=1)
            else:
                num = int(num_str) + 1
                self.summary = re.sub(pattern, f"[CONFLICT {num}] ", self.summary, count=1)
