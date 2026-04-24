"""Test synchronization with ICS files."""

import shutil
import pytest
from syncalpy.calendar import Calendar
from syncalpy.config import Config
from syncalpy.protocols.ics_file import ICSFileProtocol
from syncalpy.sync import Synchronization


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
        sync = config.get_synchronizations()[0]
        sync.run()

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

        sync = config.get_synchronizations()[0]
        sync.run()
        sync.run()

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

        sync = config.get_synchronizations()[0]
        sync.run()

        assert "event1@example.com" in cal1_path.read_text()
        assert "event2@example.com" in cal2_path.read_text()

        cal1 = sync.get_cal1()
        cal1.events = [e for e in cal1.events if e.uid != "event2@example.com"]
        cal1.finalize()

        sync.run()

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
        sync = config.get_synchronizations()[0]
        sync.run()

        cal1 = sync.get_cal1()
        cal1.events[0].summary = "Modified by cal1"
        cal1.finalize()

        cal2 = sync.get_cal2()
        cal2.events[0].summary = "Modified by cal2"
        cal2.finalize()

        sync.run()

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert cal1_content.count("BEGIN:VEVENT") == 2
        assert cal2_content.count("BEGIN:VEVENT") == 2
        assert cal1_content.count("[CONFLICT]") == 2
        assert cal2_content.count("[CONFLICT]") == 2

    def test_sync_with_filter(self, tmp_path):
        """Filter should not remove events from source calendar."""
        cal1_path = tmp_path / "calendar1.ics"
        cal2_path = tmp_path / "calendar2.ics"

        create_ics_file(str(cal1_path), "event1@example.com", "WORK Meeting", "20260421T140000")
        create_ics_file(str(cal2_path), "event2@example.com", "PRIVATE Lunch", "20260422T120000")

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
        sync = config.get_synchronizations()[0]
        sync.run()

        assert "event1@example.com" in cal1_path.read_text()
        assert "event2@example.com" in cal1_path.read_text()
        assert "event1@example.com" in cal2_path.read_text()
        assert "event2@example.com" in cal2_path.read_text()

        config._config["synchronizations"][0]["calendar1"]["filters"] = [
            {"name": "regexp_summary", "pattern": "^WORK"}
        ]
        sync.run()

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert "event1@example.com" in cal1_content
        assert "event2@example.com" in cal1_content
        assert "event1@example.com" in cal2_content
        assert "event2@example.com" not in cal2_content

    def test_sync_cal1_to_cal2(self, tmp_path):
        """Sync mode cal1_to_cal2 only propagates cal1 to cal2, not cal2 to cal1."""
        cal1_path = tmp_path / "calendar1.ics"
        cal2_path = tmp_path / "calendar2.ics"

        create_ics_file(str(cal1_path), "event1@example.com", "Meeting", "20260421T140000")
        create_ics_file(str(cal2_path), "event2@example.com", "Lunch", "20260422T120000")

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text(f"""synchronizations:
  - name: "test-sync"
    sync_mode: "cal1_to_cal2"
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
        sync = config.get_synchronizations()[0]
        sync.run()

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert "event1@example.com" in cal1_content
        assert "event2@example.com" not in cal1_content
        assert "event1@example.com" in cal2_content
        assert "event2@example.com" in cal2_content

    def test_sync_cal2_to_cal1(self, tmp_path):
        """Sync mode cal2_to_cal1 only propagates cal2 to cal1, not cal1 to cal2."""
        cal1_path = tmp_path / "calendar1.ics"
        cal2_path = tmp_path / "calendar2.ics"

        create_ics_file(str(cal1_path), "event1@example.com", "Meeting", "20260421T140000")
        create_ics_file(str(cal2_path), "event2@example.com", "Lunch", "20260422T120000")

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text(f"""synchronizations:
  - name: "test-sync"
    sync_mode: "cal2_to_cal1"
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
        sync = config.get_synchronizations()[0]
        sync.run()

        cal1_content = cal1_path.read_text()
        cal2_content = cal2_path.read_text()

        assert "event1@example.com" in cal1_content
        assert "event2@example.com" in cal1_content
        assert "event1@example.com" not in cal2_content
        assert "event2@example.com" in cal2_content
