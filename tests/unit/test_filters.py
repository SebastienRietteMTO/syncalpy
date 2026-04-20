"""Unit tests for filters."""

import pytest
from datetime import datetime, timedelta
from syncalpy.event import CalendarEvent
from syncalpy.filters.future_only import FutureOnlyFilter
from syncalpy.filters.regexp import RegexpFilter


def make_event(uid, summary, days_from_now=0):
    """Helper to create test events."""
    return CalendarEvent(
        uid=uid,
        summary=summary,
        start=datetime.now() + timedelta(days=days_from_now),
    )


class TestFutureOnlyFilter:
    """Tests for FutureOnlyFilter."""

    def test_filter_future_events(self):
        """Keep only future events."""
        events = [
            make_event("1", "Future", 7),
            make_event("2", "Past", -7),
        ]

        filter_obj = FutureOnlyFilter(reference_time=datetime.now())
        result = filter_obj.filter(events)

        assert len(result) == 1
        assert result[0].uid == "1"

    def test_filter_no_start_date(self):
        """Keep events without start date."""
        events = [
            CalendarEvent(uid="1", summary="No date", start=None),
        ]

        filter_obj = FutureOnlyFilter(reference_time=datetime.now())
        result = filter_obj.filter(events)

        assert len(result) == 1

    def test_filter_all_past(self):
        """Return empty when all events are past."""
        events = [
            make_event("1", "Past", -7),
        ]

        filter_obj = FutureOnlyFilter(reference_time=datetime.now())
        result = filter_obj.filter(events)

        assert len(result) == 0


class TestRegexpFilter:
    """Tests for RegexpFilter."""

    def test_filter_by_title(self):
        """Filter by title field."""
        events = [
            make_event("1", "Meeting with team", 1),
            make_event("2", "Lunch with friend", 1),
        ]

        filter_obj = RegexpFilter(pattern="meeting", field="title")
        result = filter_obj.filter(events)

        assert len(result) == 1
        assert result[0].uid == "1"

    def test_filter_by_description(self):
        """Filter by description field."""
        events = [
            CalendarEvent(uid="1", summary="Event 1", description="Important meeting", start=datetime.now()),
            CalendarEvent(uid="2", summary="Event 2", description="Casual lunch", start=datetime.now()),
        ]

        filter_obj = RegexpFilter(pattern="meeting", field="description")
        result = filter_obj.filter(events)

        assert len(result) == 1
        assert result[0].uid == "1"

    def test_filter_any_field(self):
        """Filter by any field."""
        events = [
            CalendarEvent(uid="1", summary="Meeting", description="Discuss team", start=datetime.now()),
            CalendarEvent(uid="2", summary="Lunch", description="With team", start=datetime.now()),
        ]

        filter_obj = RegexpFilter(pattern="team", field="any")
        result = filter_obj.filter(events)

        assert len(result) == 2

    def test_filter_no_match(self):
        """Return empty when no match."""
        events = [
            make_event("1", "Meeting", 1),
        ]

        filter_obj = RegexpFilter(pattern="lunch")
        result = filter_obj.filter(events)

        assert len(result) == 0

    def test_filter_case_insensitive(self):
        """Case insensitive matching."""
        events = [
            make_event("1", "MEETING", 1),
            make_event("2", "meeting", 1),
        ]

        filter_obj = RegexpFilter(pattern="meeting")
        result = filter_obj.filter(events)

        assert len(result) == 2