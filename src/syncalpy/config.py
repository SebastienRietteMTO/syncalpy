"""Configuration management."""

from pathlib import Path
from typing import Any, Dict, List

import yaml
from .calendar import Calendar
from .filters import get_filter
from .protocols import get_protocol


DEFAULT_CONFIG_DIR = Path.home() / ".syncalpy"


class Config:
    """Configuration manager."""

    def __init__(self, config_dir: str = None):
        """Initialize configuration.

        Args:
            config_dir: Path to config directory containing config.yaml and state/.
                        Defaults to ~/.syncalpy
        """
        if config_dir:
            config_path = Path(config_dir)
        else:
            config_path = DEFAULT_CONFIG_DIR
        self.config_file = config_path / "config.yaml"
        self.state_dir = config_path / "state"
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if not self.config_file.exists():
            self._config = {"synchronizations": []}
            return

        with open(self.config_file, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {"synchronizations": []}

    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._config, f, default_flow_style=False)

    def get_synchronizations(self) -> List[Dict[str, Any]]:
        """Get list of synchronizations."""
        return self._config.get("synchronizations", [])

    def add_synchronization(self, sync: Dict[str, Any]) -> None:
        """Add a synchronization."""
        syncs = self._config.get("synchronizations", [])
        syncs.append(sync)
        self._config["synchronizations"] = syncs
        self.save()

    def get_state_dir(self) -> Path:
        """Get state directory."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        return self.state_dir


def load_calendar_config(cal_config: Dict[str, Any]) -> Calendar:
    """Load Calendar from config dict."""
    calendar = Calendar(
        name=cal_config.get("name", "calendar"),
        url=cal_config.get("url", ""),
        protocol=cal_config.get("protocol", "ics_file"),
        username=cal_config.get("user", ""),
        password=cal_config.get("password", ""),
        filters=cal_config.get("filters", []),
    )

    return calendar


def create_protocol(calendar: Calendar):
    """Create protocol instance from calendar config."""
    protocol_class = get_protocol(calendar.protocol)
    return protocol_class(
        url=calendar.url,
        username=calendar.username,
        password=calendar.password,
    )


def apply_filters(calendar: Calendar) -> Calendar:
    """Apply filters to calendar events."""
    events = calendar.events
    for filter_config in calendar.filters:
        if isinstance(filter_config, dict):
            filter_name = filter_config.get("name")
            filter_params = {k: v for k, v in filter_config.items() if k != "name"}
            filter_obj = get_filter(filter_name, **filter_params)
            events = filter_obj.filter(events)
        elif isinstance(filter_config, str):
            filter_obj = get_filter(filter_config)
            events = filter_obj.filter(events)

    calendar.events = events
    return calendar
