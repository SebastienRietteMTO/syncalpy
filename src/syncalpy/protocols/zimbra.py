"""Zimbra protocol for calendar access."""

import re
from typing import Optional

import requests
from dateutil import parser as date_parser
from ..calendar import Calendar
from ..event import CalendarEvent, parse_vevent


class ZimbraProtocol(Calendar):
    """Zimbra protocol for calendar access via REST API."""

    def __init__(self, url: str, username: str = "", password: str = ""):
        """Initialize Zimbra protocol.

        Args:
            url: Zimbra server URL
            username: Username for authentication
            password: Password for authentication
        """
        super().__init__()
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)

        fetched = self._fetch()
        self.events = fetched.events

    def _fetch(self) -> Calendar:
        """Fetch calendar from Zimbra server."""
        calendar_url = f"{self.url}/home/{self.username}/calendar"

        try:
            response = self.session.get(
                calendar_url,
                params={"format": "ics"},
                timeout=30,
            )
            response.raise_for_status()

            return self._parse_ics(response.text)
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch calendar from Zimbra: {e}") from e

    def add_event(self, event: CalendarEvent) -> None:
        """Add an event to the calendar and push to Zimbra server."""
        super().add_event(event)
        self._push_event_to_server(event)

    def _push_event_to_server(self, event: CalendarEvent) -> None:
        """Push a single event to Zimbra server."""
        ics_content = self._build_ics_event(event)

        calendar_url = f"{self.url}/home/{self.username}/calendar"
        files = {"file": ("calendar.ics", ics_content, "text/calendar")}

        try:
            response = self.session.post(
                calendar_url,
                files=files,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to push event to Zimbra: {e}") from e

    def remove_event(self, uid: str) -> None:
        """Remove an event from the calendar and delete from Zimbra server."""
        super().remove_event(uid)
        self._remove_event_from_server(uid)

    def _remove_event_from_server(self, uid: str) -> None:
        """Delete an event from Zimbra server."""
        calendar_url = f"{self.url}/home/{self.username}/calendar"

        ics_content = self._build_ics_event_for_deletion(uid)
        files = {"file": ("calendar.ics", ics_content, "text/calendar")}

        try:
            response = self.session.post(
                calendar_url,
                files=files,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to delete event from Zimbra: {e}") from e

    def _parse_ics(self, content: str) -> Calendar:
        """Parse ICS content to Calendar."""
        calendar = Calendar()

        pattern = r"BEGIN:VEVENT.*?END:VEVENT"
        matches = re.findall(pattern, content, re.DOTALL)

        for vevent in matches:
            event = self._parse_vevent(vevent)
            if event:
                calendar.add_event(event)

        return calendar

    def _parse_vevent(self, vevent: str) -> Optional[CalendarEvent]:
        """Parse a VEVENT block to CalendarEvent."""
        return parse_vevent(vevent)

    def _build_ics_event(self, event: CalendarEvent) -> str:
        """Build ICS content for a single event."""
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Syncalpy//EN"]
        lines.append(event.to_ical())
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def _build_ics_event_for_deletion(self, uid: str) -> str:
        """Build ICS content for event deletion."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Syncalpy//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            "STATUS:CANCELLED",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
        return "\r\n".join(lines) + "\r\n"

    def _build_ics(self, calendar: Calendar) -> str:
        """Build ICS content from calendar."""
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Syncalpy//EN"]

        for event in calendar.events:
            lines.append(event.to_ical())

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"
