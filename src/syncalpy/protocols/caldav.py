"""CalDAV protocol for calendar access."""

import caldav
from typing import Optional

from ..calendar import Calendar
from ..event import CalendarEvent


class CalDAVProtocol(Calendar):
    """CalDAV protocol for remote calendar access using caldav package."""

    def __init__(self, url: str, username: str = "", password: str = ""):
        """Initialize CalDAV protocol.

        Args:
            url: CalDAV server URL
            username: Username for authentication
            password: Password for authentication
        """
        super().__init__()
        self.url = url
        self.username = username
        self.password = password

        self.client = caldav.DAVClient(
            url=url,
            username=username,
            password=password,
        ).calendar(url=url)

        self._fetch()

    def _fetch(self) -> None:
        """Fetch calendar from CalDAV server."""
        try:
            for event in self.client.events():
                cal_event = CalendarEvent()
                cal_event.update(event.icalendar_component)
                self.events.append(cal_event)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch calendar from CalDAV: {e}") from e

    def add_event(self, event_or_calendar) -> None:
        """Add an event or calendar to the calendar and push to CalDAV server."""
        super().add_event(event_or_calendar)

        if isinstance(event_or_calendar, CalendarEvent):
            ics_data = event_or_calendar.to_ical()
        elif isinstance(event_or_calendar, Calendar):
            ics_data = event_or_calendar.to_ical(include_calendar_wrapper=False)
        else:
            raise TypeError("add_event expects a CalendarEvent or Calendar instance")

        try:
            self.client.save_event(ics_data)
        except Exception as e:
            uid = event_or_calendar.uid if isinstance(event_or_calendar, CalendarEvent) else "multiple"
            raise RuntimeError(f"Failed to push event {uid} to CalDAV: {e}") from e

    def remove_event(self, uid: str) -> None:
        """Remove an event from the calendar and delete from CalDAV server."""
        events_with_uid = self.select_events_by_uid(uid)
        if not events_with_uid.events:
            return

        super().remove_event(uid)

        try:
            event_obj = self.client.event(uid)
            if event_obj:
                event_obj.delete()
        except Exception as e:
            raise RuntimeError(f"Failed to delete event {uid} from CalDAV: {e}") from e
