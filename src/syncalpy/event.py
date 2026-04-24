"""Event model for calendar events."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid
import re
from dateutil import parser as date_parser


@dataclass
class CalendarEvent:
    """Represents a calendar event."""

    uid: str
    summary: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    _hidden: bool = False

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

    @staticmethod
    def generate_uid() -> str:
        """Generate a unique identifier for an event."""
        return uuid.uuid4().hex

    def to_ical(self) -> str:
        """Convert event to ICS format."""
        lines = [
            "BEGIN:VEVENT",
            f"UID:{self.uid}",
            f"SUMMARY:{self.summary}",
        ]

        if self.start:
            lines.append(f"DTSTART:{self._format_datetime(self.start)}")

        if self.end:
            lines.append(f"DTEND:{self._format_datetime(self.end)}")

        if self.description:
            lines.append(f"DESCRIPTION:{self.description}")

        if self.location:
            lines.append(f"LOCATION:{self.location}")

        if self.created:
            lines.append(f"CREATED:{self._format_datetime(self.created)}")

        if self.modified:
            lines.append(f"LAST-MODIFIED:{self._format_datetime(self.modified)}")

        lines.append("END:VEVENT")
        return "\r\n".join(lines)

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        """Format datetime for ICS."""
        return dt.strftime("%Y%m%dT%H%M%S")

    def __hash__(self):
        """Hash based on UID."""
        return hash(self.uid)

    def __eq__(self, other):
        """Compare all public fields."""
        if not isinstance(other, CalendarEvent):
            return False
        return (
            self.uid == other.uid
            and self.summary == other.summary
            and self.start == other.start
            and self.end == other.end
            and self.description == other.description
            and self.location == other.location
            and self.created == other.created
            and self.modified == other.modified
        )

    def set(self, other: "CalendarEvent") -> None:
        """Set this event to match another event."""
        self.summary = other.summary
        self.start = other.start
        self.end = other.end
        self.description = other.description
        self.location = other.location
        self.created = other.created
        self.modified = other.modified
        self.raw_ics = other.raw_ics
        self.source = other.source

    def copy(self) -> "CalendarEvent":
        """Return a copy of this event."""
        return CalendarEvent(
            uid=self.uid,
            summary=self.summary,
            start=self.start,
            end=self.end,
            description=self.description,
            location=self.location,
            created=self.created,
            modified=self.modified,
            raw_ics=self.raw_ics,
            source=self.source,
            _hidden=self._hidden,
        )

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


def parse_vevent(vevent: str) -> Optional["CalendarEvent"]:
    """Parse a VEVENT block to CalendarEvent."""
    from icalendar import Calendar

    try:
        cal = Calendar.from_ical(vevent)
    except Exception:
        return None

    component = cal.walk()
    if not component:
        return None

    component = component[0]
    uid = component.get("uid")
    if not uid:
        return None

    dtstart = component.get("dtstart")
    dtend = component.get("dtend")

    return CalendarEvent(
        uid=str(uid),
        summary=str(component.get("summary", "")),
        start=dtstart.dt if hasattr(dtstart, 'dt') else None,
        end=dtend.dt if hasattr(dtend, 'dt') else None,
        description=str(component.get("description")) if component.get("description") else None,
        location=str(component.get("location")) if component.get("location") else None,
    )
