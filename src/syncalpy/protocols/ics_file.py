"""ICS file protocol for local calendar files and HTTP URLs."""

import os
import re
from typing import Optional

import requests
from dateutil import parser as date_parser
from ..calendar import Calendar
from ..event import CalendarEvent, parse_vevent


class ICSFileProtocol(Calendar):
    """Protocol for reading/writing ICS files from local path or HTTP URL."""

    def __init__(self, url: str, username: str = "", password: str = ""):
        """Initialize ICS file protocol.

        Args:
            url: Path to the ICS file or HTTP/HTTPS URL
            username: Not used (for compatibility)
            password: Not used (for compatibility)
        """
        super().__init__()
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
            return Calendar()

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

    def _build_ics(self, calendar: Calendar) -> str:
        """Build ICS content from calendar."""
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Syncalpy//EN"]

        for event in calendar.events:
            lines.append(event.to_ical())

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"
