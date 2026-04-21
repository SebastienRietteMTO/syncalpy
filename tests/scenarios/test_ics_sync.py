"""Test synchronization with ICS files."""

import shutil
import pytest
from syncalpy.calendar import Calendar
from syncalpy.config import Config
from syncalpy.protocols.ics_file import ICSFileProtocol
from syncalpy.sync import run_synchronization


def create_ics_file(path: str, uid: str, summary: str, date: str, location: str = ""):
    """Create a simple ICS file."""
    location_line = f"LOCATION:{location}\n" if location else ""
    content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Syncalpy//EN
BEGIN:VEVENT
UID:{uid}
SUMMARY:{summary}
DTSTART:{date}
DTEND:{date}
{location_line}END:VEVENT
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

    def test_sync_after_manual_delete(self, tmp_path):
        """Manual deletion of event from calendar1 should propagate to calendar2."""
        cal1_path = tmp_path / "calendar1.ics"
        cal2_path = tmp_path / "calendar2.ics"

        create_ics_file(str(cal1_path), "event1@example.com", "Meeting", "20260421T140000", "Room A")
        create_ics_file(str(cal2_path), "event2@example.com", "Lunch", "20260422T120000", "Restaurant")

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

        assert "event1@example.com" in cal1_path.read_text()
        assert "event2@example.com" in cal2_path.read_text()

        cal1 = ICSFileProtocol(str(cal1_path)).fetch()
        cal1.events = [e for e in cal1.events if e.uid != "event2@example.com"]
        ICSFileProtocol(str(cal1_path)).push(cal1)

        run_synchronization(config.get_synchronizations()[0], config)

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert "event2@example.com" not in cal1_content
        assert "event2@example.com" not in cal2_content
        assert "event1@example.com" in cal1_content
        assert "event1@example.com" in cal2_content

    def test_sync_conflict_both_modify_same_event(self, tmp_path):
        """When same event modified in both files, create conflict event in both."""
        cal1_path = tmp_path / "calendar1.ics"
        cal2_path = tmp_path / "calendar2.ics"

        create_ics_file(str(cal1_path), "event1@example.com", "Meeting", "20260421T140000", "Room A")
        create_ics_file(str(cal2_path), "event1@example.com", "Meeting", "20260421T140000", "Room A")

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

        cal1 = ICSFileProtocol(str(cal1_path)).fetch()
        cal1.events[0].summary = "Modified by cal1"
        ICSFileProtocol(str(cal1_path)).push(cal1)

        cal2 = ICSFileProtocol(str(cal2_path)).fetch()
        cal2.events[0].summary = "Modified by cal2"
        ICSFileProtocol(str(cal2_path)).push(cal2)

        run_synchronization(config.get_synchronizations()[0], config)

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert "Modified by cal1" in cal1_content
        assert "Modified by cal2" in cal1_content
        assert "event1@example.com_conflict" in cal1_content

        assert "Modified by cal2" in cal2_content
        assert "Modified by cal1" in cal2_content
        assert "event1@example.com_conflict" in cal2_content

    def test_sync_conflict_delete_cal1_modify_cal2(self, tmp_path):
        """When event deleted in cal1 but modified in cal2, modification wins."""
        cal1_path = tmp_path / "calendar1.ics"
        cal2_path = tmp_path / "calendar2.ics"

        create_ics_file(str(cal1_path), "event1@example.com", "Meeting", "20260421T140000", "Room A")
        create_ics_file(str(cal2_path), "event1@example.com", "Meeting", "20260421T140000", "Room A")

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

        cal1 = ICSFileProtocol(str(cal1_path)).fetch()
        cal1.events = []
        ICSFileProtocol(str(cal1_path)).push(cal1)

        cal2 = ICSFileProtocol(str(cal2_path)).fetch()
        cal2.events[0].summary = "New title"
        ICSFileProtocol(str(cal2_path)).push(cal2)

        run_synchronization(config.get_synchronizations()[0], config)

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert "event1@example.com" in cal1_content
        assert "New title" in cal1_content
        assert "event1@example.com" in cal2_content
        assert "New title" in cal2_content