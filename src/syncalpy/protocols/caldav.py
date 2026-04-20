"""CalDAV protocol for calendar access."""

import re
from typing import Optional

import requests
from dateutil import parser as date_parser
from ..calendar import Calendar
from ..event import CalendarEvent


class CalDAVProtocol:
    """CalDAV protocol for remote calendar access."""

    def __init__(self, url: str, username: str = "", password: str = ""):
        """Initialize CalDAV protocol.

        Args:
            url: CalDAV server URL
            username: Username for authentication
            password: Password for authentication
        """
        self.url = url
        self.username = username
        self.password = password
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)

    def fetch(self) -> Calendar:
        """Fetch calendar from CalDAV server."""
        headers = {
            "Content-Type": "application/xml",
            "Depth": "1",
        }
        body = """<?xml version="1.0" encoding="UTF-8"?>
        <d:propfind xmlns:d="DAV:">
            <d:prop>
                <d:displayname/>
                <caldav:calendar-data xmlns:caldav="urn:ietf:params:xml:ns:caldav"/>
            </d:prop>
        </d:propfind>"""

        try:
            response = self.session.request(
                "REPORT",
                self.url,
                headers=headers,
                data=body,
                timeout=30,
            )
            response.raise_for_status()
            return self._parse_response(response.text)
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch calendar from CalDAV: {e}") from e

    def push(self, calendar: Calendar) -> None:
        """Push calendar changes to CalDAV server."""
        for event in calendar.events:
            ics_data = self._build_ics(event)
            uid = event.uid

            headers = {
                "Content-Type": "application/calendar+xml",
                "If-Match": "*",
            }

            response = self.session.put(
                f"{self.url}/{uid}.ics",
                headers=headers,
                data=ics_data,
                timeout=30,
            )
            response.raise_for_status()

    def _parse_response(self, response_text: str) -> Calendar:
        """Parse CalDAV response to Calendar."""
        calendar = Calendar(name="caldav", protocol="caldav")

        pattern = r"BEGIN:VEVENT.*?END:VEVENT"
        matches = re.findall(pattern, response_text, re.DOTALL)

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
            source="caldav",
        )

    def _build_ics(self, event: CalendarEvent) -> str:
        """Build ICS data from event."""
        return event.to_ical()
