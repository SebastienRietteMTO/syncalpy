"""Event model for calendar events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


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
    raw_ics: str = ""
    source: str = ""

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
        """Equality based on UID."""
        if not isinstance(other, CalendarEvent):
            return False
        return self.uid == other.uid
