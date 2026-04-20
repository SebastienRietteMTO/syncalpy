"""Unit tests for calendar model."""

import pytest
from datetime import datetime, timedelta
from syncalpy.calendar import Calendar
from syncalpy.event import CalendarEvent


class TestCalendar:
    """Tests for Calendar model."""

    def test_add_event(self):
        """Add event to calendar."""
        calendar = Calendar(name="test")
        event = CalendarEvent(uid="1", summary="Test", start=datetime.now())

        calendar.add_event(event)

        assert len(calendar.events) == 1
        assert calendar.get_event_by_uid("1") == event

    def test_remove_event(self):
        """Remove event from calendar."""
        calendar = Calendar(name="test")
        event = CalendarEvent(uid="1", summary="Test", start=datetime.now())
        calendar.add_event(event)

        result = calendar.remove_event("1")

        assert result is True
        assert len(calendar.events) == 0

    def test_remove_nonexistent(self):
        """Remove nonexistent event returns False."""
        calendar = Calendar(name="test")

        result = calendar.remove_event("1")

        assert result is False

    def test_diff_added(self):
        """Diff detects added events in self not in other."""
        old_cal = Calendar(name="test")
        new_cal = Calendar(name="test")
        new_event = CalendarEvent(uid="1", summary="New", start=datetime.now())
        new_cal.add_event(new_event)

        diff = new_cal.diff(old_cal)

        assert len(diff["added"]) == 1
        assert diff["added"][0].uid == "1"

    def test_diff_removed(self):
        """Diff detects removed events (old not in new)."""
        old_cal = Calendar(name="test")
        old_event = CalendarEvent(uid="1", summary="Old", start=datetime.now())
        old_cal.add_event(old_event)

        new_cal = Calendar(name="test")

        diff = old_cal.diff(new_cal)

        assert len(diff["added"]) == 1
        assert diff["added"][0].uid == "1"

    def test_diff_modified(self):
        """Diff detects modified events."""
        old_cal = Calendar(name="test")
        old_event = CalendarEvent(uid="1", summary="Old", start=datetime.now())
        old_cal.add_event(old_event)

        new_cal = Calendar(name="test")
        new_event = CalendarEvent(uid="1", summary="New", start=datetime.now())
        new_cal.add_event(new_event)

        diff = old_cal.diff(new_cal)

        assert len(diff["modified"]) == 1


class TestEvent:
    """Tests for CalendarEvent model."""

    def test_generate_uid(self):
        """Generate unique ID."""
        uid1 = CalendarEvent.generate_uid()
        uid2 = CalendarEvent.generate_uid()

        assert uid1 != uid2

    def test_to_ical(self):
        """Convert event to ICS format."""
        event = CalendarEvent(
            uid="test-123",
            summary="Test Event",
            start=datetime(2024, 1, 15, 10, 0, 0),
            end=datetime(2024, 1, 15, 11, 0, 0),
            description="Description",
            location="Location",
        )

        ics = event.to_ical()

        assert "BEGIN:VEVENT" in ics
        assert "UID:test-123" in ics
        assert "SUMMARY:Test Event" in ics
        assert "DESCRIPTION:Description" in ics
        assert "LOCATION:Location" in ics
        assert "END:VEVENT" in ics

    def test_equality(self):
        """Event equality based on UID."""
        event1 = CalendarEvent(uid="1", summary="Test", start=datetime.now())
        event2 = CalendarEvent(uid="1", summary="Different", start=datetime.now())
        event3 = CalendarEvent(uid="2", summary="Test", start=datetime.now())

        assert event1 == event2
        assert event1 != event3
