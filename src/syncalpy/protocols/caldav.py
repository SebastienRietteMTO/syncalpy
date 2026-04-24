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
        super().__init__(name="caldav", protocol="caldav")
        self.url = url
        self.username = username
        self.password = password

        self.client = caldav.DAVClient(
            url=url,
            username=username,
            password=password,
        ).calendar(url=url)

        fetched = self._fetch()
        self.events = fetched.events

    def _fetch(self) -> Calendar:
        """Fetch calendar from CalDAV server."""
        try:
            result = Calendar(name="caldav", protocol="caldav")
            for event in self.client.events():
                cal_event = self._parse_event(event)
                if cal_event:
                    result.add_event(cal_event)

            return result
        except Exception as e:
            raise RuntimeError(f"Failed to fetch calendar from CalDAV: {e}") from e

    def add_event(self, event: CalendarEvent) -> None:
        """Add an event to the calendar and push to CalDAV server."""
        super().add_event(event)

        ics_data = self._build_ics_event(event)

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

    def _parse_event(self, event) -> Optional[CalendarEvent]:
        """Parse caldav event to CalendarEvent."""
        try:
            ical_component = event.icalendar_component

            uid = str(ical_component.get("uid", ""))
            if not uid:
                return None

            summary = str(ical_component.get("summary", ""))

            dtstart = ical_component.get("dtstart")
            start = dtstart.dt if dtstart else None

            dtend = ical_component.get("dtend")
            end = dtend.dt if dtend else None

            description = ical_component.get("description")
            description = str(description) if description else None

            location = ical_component.get("location")
            location = str(location) if location else None

            return CalendarEvent(
                uid=uid,
                summary=summary,
                start=start,
                end=end,
                description=description,
                location=location,
                raw_ics=str(ical_component),
                source="caldav",
            )
        except Exception:
            return None

    def _build_ics_event(self, event: CalendarEvent) -> str:
        """Build ICS data for a single event."""
        return event.to_ical()
