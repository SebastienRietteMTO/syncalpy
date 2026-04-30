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

    def add_event(self, event: CalendarEvent) -> None:
        """Add an event to the calendar and push to CalDAV server."""
        super().add_event(event)

        ics_data = event.to_ical()

        try:
            self.client.save_event(ics_data)
        except Exception as e:
            raise RuntimeError(f"Failed to push event {event.uid} to CalDAV: {e}") from e

    def remove_event(self, uid: str) -> None:
        """Remove an event from the calendar and delete from CalDAV server."""
        event = self.get_event_by_uid(uid)
        if not event:
            return

        super().remove_event(uid)

        try:
            event_obj = self.client.event(uid)
            if event_obj:
                event_obj.delete()
        except Exception as e:
            raise RuntimeError(f"Failed to delete event {uid} from CalDAV: {e}") from e
