"""Zimbra protocol for calendar access."""

import re
from typing import Optional

import requests
from ..calendar import Calendar
from ..event import CalendarEvent


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

        self._fetch()

    def _fetch(self) -> None:
        """Fetch calendar from Zimbra server."""
        calendar_url = f"{self.url}/home/{self.username}/calendar"

        try:
            response = self.session.get(
                calendar_url,
                params={"format": "ics"},
                timeout=30,
            )
            response.raise_for_status()

            self.from_ical(response.text)
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch calendar from Zimbra: {e}") from e

    def add_event(self, event_or_calendar) -> None:
        """Add an event or calendar to the calendar and push to Zimbra server."""
        super().add_event(event_or_calendar)

        if isinstance(event_or_calendar, CalendarEvent):
            # Single event - use full ICS format
            ics_content = Calendar([event_or_calendar]).to_ical()
        elif isinstance(event_or_calendar, Calendar):
            # Calendar - output events only without VCALENDAR wrapper
            ics_content = event_or_calendar.to_ical(include_calendar_wrapper=False)
        else:
            raise TypeError("add_event expects a CalendarEvent or Calendar instance")

        calendar_url = f"{self.url}/home/{self.username}/calendar"
        files = {"file": ("calendar.ics", ics_content, "text/calendar")}

        if isinstance(event_or_calendar, CalendarEvent):
            print('ADD', event_or_calendar.to_ical())
        else:
            print('ADD', event_or_calendar.to_ical(include_calendar_wrapper=False))
        #try:
        #    response = self.session.post(
        #        calendar_url,
        #        files=files,
        #        timeout=30,
        #    )
        #    response.raise_for_status()
        #except requests.RequestException as e:
        #    raise RuntimeError(f"Failed to push event to Zimbra: {e}") from e

    def remove_event(self, uid: str) -> None:
        """Remove an event from the calendar and delete from Zimbra server."""
        super().remove_event(uid)
        calendar_url = f"{self.url}/home/{self.username}/calendar"

        ics_content = self._build_ics_event_for_deletion(uid)
        files = {"file": ("calendar.ics", ics_content, "text/calendar")}

        print('REMOVE', uid)
        #try:
        #    response = self.session.post(
        #        calendar_url,
        #        files=files,
        #        timeout=30,
        #    )
        #    response.raise_for_status()
        #except requests.RequestException as e:
        #    raise RuntimeError(f"Failed to delete event from Zimbra: {e}") from e

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

    # Alternative deletion methods to consider:
    # 1. REST DELETE endpoint:
    #    response = self.session.delete(
    #        f"{self.url}/home/{self.username}/calendar",
    #        params={"fmt": "ics", "id": uid},
    #        timeout=30,
    #    )
    #
    # 2. SOAP API approach:
    #    soap_body = f"""<soap:Envelope>
    #      <soap:Body>
    #        <DeleteAppointmentRequest>
    #          <appointment id="{uid}"/>
    #        </DeleteAppointmentRequest>
    #      </soap:Body>
    #    </soap:Envelope>"""
    #    response = self.session.post(
    #        f"{self.url}/service/soap",
    #        data=soap_body,
    #        headers={"Content-Type": "application/soap+xml"},
    #        timeout=30,
    #    )
