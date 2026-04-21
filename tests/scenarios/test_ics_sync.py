"""Test synchronization with ICS files."""

import os
import tempfile
import pytest
from syncalpy.calendar import Calendar
from syncalpy.config import Config
from syncalpy.sync import run_synchronization


def create_ics_file(path: str, uid: str, summary: str, date: str):
    """Create a simple ICS file."""
    content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Syncalpy//EN
BEGIN:VEVENT
UID:{uid}
SUMMARY:{summary}
DTSTART:{date}
DTEND:{date}
END:VEVENT
END:VCALENDAR
"""
    with open(path, "w") as f:
        f.write(content)


class TestICSFileSync:
    """Test synchronization between ICS files."""

    def test_sync_two_ics_files(self, tmp_path):
        """Two ICS files should sync events bidirectionally."""
        cal1_path = tmp_path / "calendar1.ics"
        cal2_path = tmp_path / "calendar2.ics"

        create_ics_file(str(cal1_path), "event1@example.com", "Meeting", "20260421T140000")
        create_ics_file(str(cal2_path), "event2@example.com", "Lunch", "20260422T120000")

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text(f"""synchronizations:
  - name: "test-sync"
    calendar1:
      name: "calendar1"
      protocol: "ics_file"
      url: "{cal1_path}"
    calendar2:
      name: "calendar2"
      protocol: "ics_file"
      url: "{cal2_path}"
""")

        config = Config(str(config_dir))
        run_synchronization(config.get_synchronizations()[0], config)

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert "event1@example.com" in cal1_content
        assert "event2@example.com" in cal1_content
        assert "event1@example.com" in cal2_content
        assert "event2@example.com" in cal2_content

    def test_sync_after_first_run(self, tmp_path):
        """Second sync should not duplicate events."""
        cal1_path = tmp_path / "calendar1.ics"
        cal2_path = tmp_path / "calendar2.ics"

        create_ics_file(str(cal1_path), "event1@example.com", "Meeting", "20260421T140000")
        create_ics_file(str(cal2_path), "event2@example.com", "Lunch", "20260422T120000")

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text(f"""synchronizations:
  - name: "test-sync"
    calendar1:
      name: "calendar1"
      protocol: "ics_file"
      url: "{cal1_path}"
    calendar2:
      name: "calendar2"
      protocol: "ics_file"
      url: "{cal2_path}"
""")

        config = Config(str(config_dir))

        run_synchronization(config.get_synchronizations()[0], config)
        run_synchronization(config.get_synchronizations()[0], config)

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert cal1_content.count("BEGIN:VEVENT") == 2
        assert cal2_content.count("BEGIN:VEVENT") == 2