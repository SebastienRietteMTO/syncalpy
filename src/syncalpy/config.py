"""Configuration management."""

from pathlib import Path
from typing import Any, Dict, List, Union

import yaml
from .sync import Synchronization

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

    def get_synchronizations(self):
        """Get list of synchronizations."""
        state_dir = str(self.get_state_dir())
        return [
            Synchronization(sync, state_dir)
            for sync in self._config.get("synchronizations", [])
        ]

    def get_state_dir(self) -> Path:
        """Get state directory."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        return self.state_dir
