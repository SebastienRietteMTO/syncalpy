"""jCal protocol for calendar access."""

import json
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
        super().__init__(name="jcal", protocol="jcal")
        self.url = url
        self.username = username
        self.password = password
        self._is_http = url.startswith("http://") or url.startswith("https://")
        self.session = requests.Session()

        fetched = self._fetch()
        self.events = fetched.events

    def _fetch(self) -> Calendar:
        """Fetch calendar from jCal source."""
        if self._is_http:
            return self._fetch_http()
        else:
            return self._fetch_local()

    def _fetch_local(self) -> Calendar:
        """Fetch calendar from local file."""
        import os
        if not os.path.exists(self.url):
            return Calendar(name="jcal", protocol="jcal")

        with open(self.url, "r", encoding="utf-8") as f:
            data = json.load(f)

        return self._parse_response(data)

    def _fetch_http(self) -> Calendar:
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
            return self._parse_response(response.json())
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch calendar from jCal: {e}") from e

    def finalize(self) -> None:
        """Finalize the calendar - write events to jCal file."""
        super().finalize()

        if self._is_http:
            raise NotImplementedError("Finalize to HTTP URL is not supported")

        import os

        data = self._build_json()

        os.makedirs(os.path.dirname(self.url) or ".", exist_ok=True)

        with open(self.url, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _parse_response(self, data: Dict) -> Calendar:
        """Parse jCal response to Calendar."""
        calendar = Calendar(name="jcal", protocol="jcal")

        if isinstance(data, dict) and "items" in data:
            items = data.get("items", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        for item in items:
            event = self._parse_item(item)
            if event:
                calendar.add_event(event)

        return calendar

    def _parse_item(self, item: Dict) -> Optional[CalendarEvent]:
        """Parse a jCal item to CalendarEvent."""
        if not item:
            return None

        uid = item.get("uid", "")
        if not uid:
            return None

        summary = item.get("summary", "")

        start = None
        if "start" in item:
            try:
                start = date_parser.parse(str(item["start"]))
            except (ValueError, TypeError):
                pass

        end = None
        if "end" in item:
            try:
                end = date_parser.parse(str(item["end"]))
            except (ValueError, TypeError):
                pass

        description = item.get("description")
        location = item.get("location")

        return CalendarEvent(
            uid=uid,
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            source="jcal",
        )

    def _build_json_event(self, event: CalendarEvent) -> Dict:
        """Build JSON data for a single event."""
        data = {
            "uid": event.uid,
            "summary": event.summary,
        }

        if event.start:
            data["start"] = event.start.isoformat()

        if event.end:
            data["end"] = event.end.isoformat()

        if event.description:
            data["description"] = event.description

        if event.location:
            data["location"] = event.location

        return data

    def _build_json(self) -> Dict:
        """Build JSON data from calendar."""
        return {
            "items": [
                self._build_json_event(event)
                for event in self.events
            ]
        }
