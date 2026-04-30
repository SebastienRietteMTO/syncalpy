"""ICS file protocol for local calendar files and HTTP URLs."""

import os

import requests
from ..calendar import Calendar


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

        self._fetch()

    def _fetch(self) -> None:
        """Fetch calendar from ICS file or HTTP URL."""
        if self._is_http:
            self._fetch_http()
        else:
            self._fetch_local()

    def _fetch_local(self) -> None:
        """Fetch calendar from local file."""
        if os.path.exists(self.url):
            with open(self.url, "r", encoding="utf-8") as f:
                content = f.read()

            self.from_ical(content)

    def _fetch_http(self) -> None:
        """Fetch calendar from HTTP URL."""
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch ICS from {self.url}: {e}")

        self.from_ical(response.text)

    def finalize(self) -> None:
        """Finalize the calendar - write events to ICS file."""
        super().finalize()

        if self._is_http:
            raise NotImplementedError("Push to HTTP URL is not supported")

        os.makedirs(os.path.dirname(self.url) or ".", exist_ok=True)

        with open(self.url, "w", encoding="utf-8") as f:
            f.write(self.to_ical())
