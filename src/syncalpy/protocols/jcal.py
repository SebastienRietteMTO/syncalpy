"""jCal protocol for calendar access."""

import json
import os
from typing import Any, Dict, Optional

import requests
from dateutil import parser as date_parser
from ..calendar import Calendar
from ..event import CalendarEvent


class JCalProtocol(Calendar):
    """jCal protocol for remote calendar access (JSON format)."""

    def __init__(self, url: str, username: str = "", password: str = ""):
        """Initialize jCal protocol.

        Args:
            url: Path to the jCal file or HTTP/HTTPS URL
            username: Not used (for compatibility)
            password: Not used (for compatibility)
        """
        super().__init__()
        self.url = url
        self.username = username
        self.password = password
        self._is_http = url.startswith("http://") or url.startswith("https://")
        self.session = requests.Session()

        self._fetch()

    def _fetch(self) -> None:
        """Fetch calendar from jCal source."""
        if self._is_http:
            self._fetch_http()
        else:
            self._fetch_local()

    def _fetch_local(self) -> None:
        """Fetch calendar from local file."""
        if os.path.exists(self.url):
            with open(self.url, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._parse_response(data)

    def _fetch_http(self) -> None:
        """Fetch calendar from HTTP URL."""
        headers = {
            "Accept": "application/json",
        }

        try:
            response = self.session.get(
                self.url,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            self._parse_response(response.json())
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch calendar from jCal: {e}") from e

    def finalize(self) -> None:
        """Finalize the calendar - write events to jCal file."""
        super().finalize()

        if self._is_http:
            raise NotImplementedError("Finalize to HTTP URL is not supported")

        data = self._build_json()

        os.makedirs(os.path.dirname(self.url) or ".", exist_ok=True)

        with open(self.url, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _parse_response(self, data: Dict) -> None:
        """Parse jCal response to Calendar."""
        if isinstance(data, dict) and "items" in data:
            items = data.get("items", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        for item in items:
            self.events.append(self._parse_item(item))

    def _parse_item(self, item: Dict) -> Optional[CalendarEvent]:
        """Parse a jCal item to CalendarEvent."""
        # Convert date/time strings to datetime objects before creating event
        date_keys = ["start", "end", "created", "last_modified"]
        for key in date_keys:
            if key in item:
                item[key] = date_parser.isoparse(item[key])

        return CalendarEvent.create(item)

    def _build_json_event(self, event: CalendarEvent) -> Dict:
        """Build JSON data for a single event."""
        data = {}
        for key in event.keys():
            if key == "DTSTART" and event.DTSTART:
                data["start"] = event.DTSTART.isoformat()
            elif key == "DTEND" and event.DTEND:
                data["end"] = event.DTEND.isoformat()
            elif key == "DTSTAMP":
                continue
            else:
                value = event.get(key)
                if value:
                    data[key.lower()] = str(value)

        return data

    def _build_json(self) -> Dict:
        """Build JSON data from calendar."""
        return {
            "items": [
                self._build_json_event(event)
                for event in self.events
            ]
        }
