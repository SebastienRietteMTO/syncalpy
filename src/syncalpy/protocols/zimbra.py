"""Zimbra protocol for calendar access."""

import re
from typing import Optional

import requests
from dateutil import parser as date_parser
from ..calendar import Calendar
from ..event import CalendarEvent


class ZimbraProtocol:
    """Zimbra protocol for calendar access via REST API."""

    def __init__(self, url: str, username: str = "", password: str = ""):
        """Initialize Zimbra protocol.

        Args:
            url: Zimbra server URL
            username: Username for authentication
            password: Password for authentication
        """
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)

    def fetch(self) -> Calendar:
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

    def push(self, calendar: Calendar) -> None:
        """Push calendar changes to Zimbra server."""
        calendar_url = f"{self.url}/home/{self.username}/calendar"

        ics_content = self._build_ics(calendar)

        files = {"file": ("calendar.ics", ics_content, "text/calendar")}

        try:
            response = self.session.post(
                calendar_url,
                files=files,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to push calendar to Zimbra: {e}") from e

    def _parse_ics(self, content: str) -> Calendar:
        """Parse ICS content to Calendar."""
        calendar = Calendar(name="zimbra", protocol="zimbra")

        pattern = r"BEGIN:VEVENT.*?END:VEVENT"
        matches = re.findall(pattern, content, re.DOTALL)

        for vevent in matches:
            event = self._parse_vevent(vevent)
            if event:
                calendar.add_event(event)

        return calendar

    def _parse_vevent(self, vevent: str) -> Optional[CalendarEvent]:
        """Parse a VEVENT block to CalendarEvent."""
        uid_match = re.search(r"UID:(.+)", vevent)
        summary_match = re.search(r"SUMMARY:(.+)", vevent)
        dtstart_match = re.search(r"DTSTART(?::|;[^:]+:)(.+)", vevent)
        dtend_match = re.search(r"DTEND(?::|;[^:]+:)(.+)", vevent)
        desc_match = re.search(r"DESCRIPTION:(.+)", vevent)
        location_match = re.search(r"LOCATION:(.+)", vevent)

        if not uid_match:
            return None

        uid = uid_match.group(1).strip()
        summary = summary_match.group(1).strip() if summary_match else ""

        start = None
        if dtstart_match:
            try:
                start = date_parser.parse(dtstart_match.group(1).strip())
            except ValueError:
                pass

        end = None
        if dtend_match:
            try:
                end = date_parser.parse(dtend_match.group(1).strip())
            except ValueError:
                pass

        description = desc_match.group(1).strip() if desc_match else None
        location = location_match.group(1).strip() if location_match else None

        return CalendarEvent(
            uid=uid,
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            raw_ics=vevent,
            source="zimbra",
        )

    def _build_ics(self, calendar: Calendar) -> str:
        """Build ICS content from calendar."""
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Syncalpy//EN"]

        for event in calendar.events:
            lines.append(event.to_ical())

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"
