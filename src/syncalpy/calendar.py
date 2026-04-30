"""Calendar model."""

from icalendar import Calendar as ICalendar
from typing import List, Optional
from .event import CalendarEvent
from .filters import get_filter


class Calendar:
    """Represents a calendar with events."""

    def __init__(self, events: Optional[List[CalendarEvent]] = None, vcalendar: Optional[str] = None):
        """Initialize calendar.

        Args:
            events: Optional list of CalendarEvent objects
            vcalendar: Optional ICS content string to parse events from
        """
        self.events: List[CalendarEvent] = []

        if events is not None and vcalendar is not None:
            raise ValueError("Cannot pass both events and vcalendar")

        if events is not None:
            self.events = events

        if vcalendar is not None:
            self.from_ical(vcalendar)

    def from_ical(self, vcalendar: str) -> None:
        """Parse ICS content string and populate events.

        Args:
            vcalendar: ICS content string to parse
        """
        cal = ICalendar.from_ical(vcalendar.encode('utf-8'))
        for component in cal.walk():
            if component.name == "VEVENT":
                event = CalendarEvent()
                event.update(component)
                if event.get("UID"):
                    self.events.append(event)

    def to_ical(self) -> str:
        """Build ICS content from calendar."""
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Syncalpy//EN"]

        for event in self.events:
            lines.append(event.to_ical())

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def get_event_by_uid(self, uid: str) -> Optional[CalendarEvent]:
        """Get an event by its UID."""
        for event in self.events:
            if event.uid == uid:
                return event
        return None

    def add_event(self, event: CalendarEvent) -> None:
        """Add an event to the calendar."""
        if self.get_event_by_uid(event.uid):
            self.remove_event(event.uid)
        self.events.append(event)

    def get_all_uids(self) -> List[str]:
        """Get the UIDs of all events except those hidden."""
        return [event.uid for event in self.events if not event.is_hidden]

    def remove_event(self, uid: str) -> bool:
        """Remove an event by UID. Returns True if removed."""
        event = self.get_event_by_uid(uid)
        if event:
            self.events.remove(event)
            return True
        return False

    def set_missing_uids(self) -> None:
        """Set UID for all events that have a missing or empty UID."""
        for event in self.events:
            if not event.uid:
                event.set_uid()

    def diff(self, other: "Calendar") -> dict:
        """Compare this calendar with another.

        Returns dict with:
        - changed: UIDs in self that are new or modified (added + modified)
        - removed: UIDs in other but not in self
        """
        self_visible = [e for e in self.events if not e.is_hidden]
        other_visible = [e for e in other.events if not e.is_hidden]

        self_uids = set(e.uid for e in self_visible)
        other_uids = set(e.uid for e in other_visible)

        added = [e.uid for e in self_visible if e.uid not in other_uids]
        removed = [e.uid for e in other_visible if e.uid not in self_uids]

        modified = []
        for self_event in self_visible:
            if self_event.uid in other_uids:
                other_event = other.get_event_by_uid(self_event.uid)
                if other_event and not self_event == other_event:
                    modified.append(self_event.uid)

        changed = list(set(added + modified))

        return {
            "changed": changed,
            "removed": removed,
        }

    def __eq__(self, other):
        """Check equality between two calendars."""
        if not isinstance(other, Calendar):
            return False
        self_uids = set(self.get_all_uids())
        other_uids = set(other.get_all_uids())
        if self_uids != other_uids:
            return False
        for self_event in self.events:
            other_event = other.get_event_by_uid(self_event.uid)
            if other_event and self_event != other_event:
                return False
        return True

    def finalize(self):
        """Finalize the calendar."""
        pass

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.finalize()
        return False

    def apply_filters(self, filters: List) -> "Calendar":
        """Apply filters to calendar events.

        Events that don't match filters are hidden.
        """
        if not filters:
            return self

        for event in self.events:
            event.hide()

        for filter_config in filters:
            if isinstance(filter_config, dict):
                filter_name = filter_config.get("name")
                filter_params = {k: v for k, v in filter_config.items() if k != "name"}
                filter_obj = get_filter(filter_name, **filter_params)
                filtered_events = filter_obj.filter(self.events)
            elif isinstance(filter_config, str):
                filter_obj = get_filter(filter_config)
                filtered_events = filter_obj.filter(self.events)
            else:
                filtered_events = []

            for event in filtered_events:
                event._hidden = False

        return self
