"""ICS file protocol for local calendar files and HTTP URLs."""

import os
import re
from typing import Optional

import requests
from dateutil import parser as date_parser
from ..calendar import Calendar
from ..event import CalendarEvent


class ICSFileProtocol(Calendar):
    """Protocol for reading/writing ICS files from local path or HTTP URL."""

    def __init__(self, url: str, username: str = "", password: str = ""):
        """Initialize ICS file protocol.

        Args:
            url: Path to the ICS file or HTTP/HTTPS URL
            username: Not used (for compatibility)
            password: Not used (for compatibility)
        """
        super().__init__(name="ics", protocol="ics_file")
        self.url = url
        self.username = username
        self.password = password
        self._is_http = url.startswith("http://") or url.startswith("https://")

        fetched = self._fetch()
        self.events = fetched.events

    def _fetch(self) -> Calendar:
        """Fetch calendar from ICS file or HTTP URL."""
        if self._is_http:
            return self._fetch_http()
        else:
            return self._fetch_local()

    def _fetch_local(self) -> Calendar:
        """Fetch calendar from local file."""
        if not os.path.exists(self.url):
            return Calendar(name="ics", protocol="ics_file")

        with open(self.url, "r", encoding="utf-8") as f:
            content = f.read()

        return self._parse_ics(content)

    def _fetch_http(self) -> Calendar:
        """Fetch calendar from HTTP URL."""
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch ICS from {self.url}: {e}")

        return self._parse_ics(response.text)

    def finalize(self) -> None:
        """Finalize the calendar - write events to ICS file."""
        super().finalize()

        if self._is_http:
            raise NotImplementedError("Push to HTTP URL is not supported")

        ics_content = self._build_ics(self)

        os.makedirs(os.path.dirname(self.url) or ".", exist_ok=True)

        with open(self.url, "w", encoding="utf-8") as f:
            f.write(ics_content)

    def _parse_ics(self, content: str) -> Calendar:
        """Parse ICS content to Calendar."""
        calendar = Calendar(name="ics", protocol="ics_file")

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
            source="ics_file",
        )

    def _build_ics(self, calendar: Calendar) -> str:
        """Build ICS content from calendar."""
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Syncalpy//EN"]

        for event in calendar.events:
            lines.append(event.to_ical())

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"
