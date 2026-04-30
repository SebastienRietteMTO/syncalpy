"""Unit tests for filters."""

import pytest
from datetime import datetime, timedelta
from syncalpy.event import CalendarEvent
from syncalpy.filters.future_only import FutureOnlyFilter
from syncalpy.filters.regexp import RegexpSummaryFilter, RegexpDescriptionFilter, RegexpLocationFilter


class TestFutureOnlyFilter:
    """Tests for FutureOnlyFilter."""

    def test_filter_future_events(self):
        """Keep only future events."""
        events = [
            CalendarEvent.create({
                "uid": "1",
                "summary": "Future",
                "start": datetime.now() + timedelta(days=7),
            }),
            CalendarEvent.create({
                "uid": "2",
                "summary": "Past",
                "start": datetime.now() + timedelta(days=-7),
            }),
        ]

        filter_obj = FutureOnlyFilter(reference_time=datetime.now())
        result = filter_obj.filter(events)

        assert len(result) == 1
        assert result[0].uid == "1"

    def test_filter_no_start_date(self):
        """Keep events without start date."""
        events = [
            CalendarEvent.create({"uid": "1", "summary": "No date", "start": None}),
        ]

        filter_obj = FutureOnlyFilter(reference_time=datetime.now())
        result = filter_obj.filter(events)

        assert len(result) == 1

    def test_filter_all_past(self):
        """Return empty when all events are past."""
        events = [
            CalendarEvent.create({
                "uid": "1",
                "summary": "Past",
                "start": datetime.now() + timedelta(days=-7),
            }),
        ]

        filter_obj = FutureOnlyFilter(reference_time=datetime.now())
        result = filter_obj.filter(events)

        assert len(result) == 0


class TestRegexpSummaryFilter:
    """Tests for RegexpSummaryFilter."""

    def test_filter_by_summary(self):
        """Filter by summary field."""
        events = [
            CalendarEvent.create({
                "uid": "1",
                "summary": "Meeting with team",
                "start": datetime.now() + timedelta(days=1),
            }),
            CalendarEvent.create({
                "uid": "2",
                "summary": "Lunch with friend",
                "start": datetime.now() + timedelta(days=1),
            }),
        ]

        filter_obj = RegexpSummaryFilter(pattern="meeting")
        result = filter_obj.filter(events)

        assert len(result) == 1
        assert result[0].uid == "1"

    def test_filter_no_match(self):
        """Return empty when no match."""
        events = [
            CalendarEvent.create({
                "uid": "1",
                "summary": "Meeting",
                "start": datetime.now() + timedelta(days=1),
            }),
        ]

        filter_obj = RegexpSummaryFilter(pattern="lunch")
        result = filter_obj.filter(events)

        assert len(result) == 0

    def test_filter_case_insensitive(self):
        """Case insensitive matching."""
        events = [
            CalendarEvent.create({
                "uid": "1",
                "summary": "MEETING",
                "start": datetime.now() + timedelta(days=1),
            }),
            CalendarEvent.create({
                "uid": "2",
                "summary": "meeting",
                "start": datetime.now() + timedelta(days=1),
            }),
        ]

        filter_obj = RegexpSummaryFilter(pattern="meeting")
        result = filter_obj.filter(events)

        assert len(result) == 2


class TestRegexpDescriptionFilter:
    """Tests for RegexpDescriptionFilter."""

    def test_filter_by_description(self):
        """Filter by description field."""
        events = [
            CalendarEvent.create({"uid": "1", "summary": "Event 1", "description": "Important meeting", "start": datetime.now()}),
            CalendarEvent.create({"uid": "2", "summary": "Event 2", "description": "Casual lunch", "start": datetime.now()}),
        ]

        filter_obj = RegexpDescriptionFilter(pattern="meeting")
        result = filter_obj.filter(events)

        assert len(result) == 1
        assert result[0].uid == "1"


class TestRegexpLocationFilter:
    """Tests for RegexpLocationFilter."""

    def test_filter_by_location(self):
        """Filter by location field."""
        events = [
            CalendarEvent.create({"uid": "1", "summary": "Event 1", "location": "Conference Room A", "start": datetime.now()}),
            CalendarEvent.create({"uid": "2", "summary": "Event 2", "location": "Cafeteria", "start": datetime.now()}),
        ]

        filter_obj = RegexpLocationFilter(pattern="conference")
        result = filter_obj.filter(events)

        assert len(result) == 1
        assert result[0].uid == "1"