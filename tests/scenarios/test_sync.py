"""Scenario tests for synchronization.

These tests cover various conflict resolution scenarios.
"""

import copy
import pytest
from datetime import datetime, timedelta
from syncalpy.calendar import Calendar
from syncalpy.event import CalendarEvent
from syncalpy.sync import Synchronization


def synchronize_calendars(prev_cal, curr_cal1, curr_cal2, sync_mode="bidirectional", filters1=None, filters2=None):
    """Synchronize two calendars using Synchronization.synchronize."""
    cal1 = copy.deepcopy(curr_cal1)
    cal2 = copy.deepcopy(curr_cal2)
    ref = copy.deepcopy(prev_cal)

    cal1.set_missing_uids()
    cal2.set_missing_uids()
    ref.set_missing_uids()

    cal1 = cal1.apply_filters(filters1 or [])
    cal2 = cal2.apply_filters(filters2 or [])

    Synchronization.synchronize(cal1, cal2, ref, sync_mode)

    return cal1, cal2


class TestSyncConflictResolution:
    """Test conflict resolution scenarios."""

    def test_no_changes(self):
        """No changes - calendars identical."""
        event = CalendarEvent.create({
            "uid": "1",
            "summary": "Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        cal1 = Calendar(events=[event])
        cal2 = Calendar(events=[event])
        prev_cal = Calendar(events=[event])

        updated1, updated2 = synchronize_calendars(prev_cal, cal1, cal2)

        assert len(updated1.events) == 1
        assert len(updated2.events) == 1
        assert updated1 == updated2

    def test_add_event_to_cal1(self):
        """Add event to calendar 1 propagates to calendar 2."""
        prev_cal = Calendar(events=[])

        event = CalendarEvent.create({
            "uid": "1",
            "summary": "New Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        curr_cal1 = Calendar(events=[event])
        curr_cal2 = Calendar(events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 1
        assert len(updated2.events) == 1
        assert updated2.get_event_by_uid("1") is not None
        assert updated1 == updated2

    def test_add_event_to_cal2(self):
        """Add event to calendar 2 propagates to calendar 1."""
        prev_cal = Calendar(events=[])

        event = CalendarEvent.create({
            "uid": "1",
            "summary": "New Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        curr_cal1 = Calendar(events=[])
        curr_cal2 = Calendar(events=[event])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 1
        assert len(updated2.events) == 1
        assert updated1.get_event_by_uid("1") is not None
        assert updated1 == updated2

    def test_delete_event_from_cal1(self):
        """Delete event from calendar 1 propagates to calendar 2."""
        event = CalendarEvent.create({
            "uid": "1",
            "summary": "Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        prev_cal = Calendar(events=[event])

        curr_cal1 = Calendar(events=[])
        curr_cal2 = Calendar(events=[event])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 0
        assert len(updated2.events) == 0
        assert updated1 == updated2

    def test_delete_event_from_cal2(self):
        """Delete event from calendar 2 propagates to calendar 1."""
        event = CalendarEvent.create({
            "uid": "1",
            "summary": "Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        prev_cal = Calendar(events=[event])

        curr_cal1 = Calendar(events=[event])
        curr_cal2 = Calendar(events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 0
        assert len(updated2.events) == 0
        assert updated1 == updated2

    def test_conflict_delete_cal1_modify_cal2(self):
        """Conflict: delete from cal1, modify in cal2."""
        old_event = CalendarEvent.create({
            "uid": "1",
            "summary": "Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        prev_cal = Calendar(events=[old_event])

        curr_cal1 = Calendar(events=[])
        event2 = CalendarEvent.create({"uid": "1", "summary": "Modified", "start": old_event.DTSTART, "end": old_event.DTEND})
        curr_cal2 = Calendar(events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 1
        assert len(updated2.events) == 1
        assert updated1 == updated2

    def test_conflict_modify_cal1_delete_cal2(self):
        """Conflict: modify in cal1, delete from cal2."""
        old_event = CalendarEvent.create({
            "uid": "1",
            "summary": "Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        prev_cal = Calendar(events=[old_event])

        event1 = CalendarEvent.create({"uid": "1", "summary": "Modified", "start": old_event.DTSTART, "end": old_event.DTEND})
        curr_cal1 = Calendar(events=[event1])
        curr_cal2 = Calendar(events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 1
        assert len(updated2.events) == 1
        assert updated1 == updated2

    def test_conflict_modify_both_titles(self):
        """Conflict: modify title on both sides - create conflict event."""
        old_event = CalendarEvent.create({
            "uid": "1",
            "summary": "Original",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        prev_cal = Calendar(events=[old_event])

        event1 = CalendarEvent.create({"uid": "1", "summary": "Modified by cal1", "start": old_event.DTSTART, "end": old_event.DTEND})
        event2 = CalendarEvent.create({"uid": "1", "summary": "Modified by cal2", "start": old_event.DTSTART, "end": old_event.DTEND})
        curr_cal1 = Calendar(events=[event1])
        curr_cal2 = Calendar(events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert updated1.get_event_by_uid("1") is not None
        assert updated2.get_event_by_uid("1") is not None
        assert len(updated1.events) == 2
        assert len(updated2.events) == 2
        assert updated1 == updated2

    def test_conflict_modify_both_dates(self):
        """Conflict: modify dates on both sides - create conflict event."""
        old_event = CalendarEvent.create({
            "uid": "1",
            "summary": "Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        prev_cal = Calendar(events=[old_event])

        event1 = CalendarEvent.create({"uid": "1", "summary": "Event",
            "start": datetime.now() + timedelta(days=2),
            "end": datetime.now() + timedelta(days=2, hours=1)})
        event2 = CalendarEvent.create({"uid": "1", "summary": "Event",
            "start": datetime.now() + timedelta(days=3),
            "end": datetime.now() + timedelta(days=3, hours=1)})
        curr_cal1 = Calendar(events=[event1])
        curr_cal2 = Calendar(events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert updated1.get_event_by_uid("1") is not None
        assert updated2.get_event_by_uid("1") is not None
        assert len(updated1.events) == 2
        assert len(updated2.events) == 2
        assert updated1 == updated2

    def test_conflict_modify_both_descriptions(self):
        """Conflict: modify description on both sides - create conflict event."""
        old_event = CalendarEvent.create({"uid": "1", "summary": "Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
            "description": "Original"})
        prev_cal = Calendar(events=[old_event])

        event1 = CalendarEvent.create({"uid": "1", "summary": "Event",
            "start": old_event.DTSTART, "end": old_event.DTEND,
            "description": "Description from cal1"})
        event2 = CalendarEvent.create({"uid": "1", "summary": "Event",
            "start": old_event.DTSTART, "end": old_event.DTEND,
            "description": "Description from cal2"})
        curr_cal1 = Calendar(events=[event1])
        curr_cal2 = Calendar(events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert updated1.get_event_by_uid("1") is not None
        assert len(updated1.events) == 2
        assert len(updated2.events) == 2
        assert updated1 == updated2

    def test_sync_multiple_events(self):
        """Multiple events sync correctly."""
        events_prev = [
            CalendarEvent.create({
                "uid": "1",
                "summary": "Event 1",
                "start": datetime.now() + timedelta(days=1),
                "end": datetime.now() + timedelta(days=1, hours=1),
            }),
            CalendarEvent.create({
                "uid": "2",
                "summary": "Event 2",
                "start": datetime.now() + timedelta(days=2),
                "end": datetime.now() + timedelta(days=2, hours=1),
            }),
        ]
        prev_cal = Calendar(events=list(events_prev))

        event_new = CalendarEvent.create({
            "uid": "3",
            "summary": "Event 3",
            "start": datetime.now() + timedelta(days=3),
            "end": datetime.now() + timedelta(days=3, hours=1),
        })
        curr_cal1 = Calendar(events=events_prev + [event_new])
        curr_cal2 = Calendar(events=events_prev)

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated2.events) == 3
        assert updated1 == updated2

    def test_bidirectional_sync(self):
        """Bidirectional sync works both ways."""
        event1 = CalendarEvent.create({
            "uid": "1",
            "summary": "Event in cal1",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        event2 = CalendarEvent.create({
            "uid": "2",
            "summary": "Event in cal2",
            "start": datetime.now() + timedelta(days=2),
            "end": datetime.now() + timedelta(days=2, hours=1),
        })
        prev_cal = Calendar(events=[])

        curr_cal1 = Calendar(events=[event1])
        curr_cal2 = Calendar(events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 2
        assert len(updated2.events) == 2
        assert updated1 == updated2

    def test_complex_conflict_all_changed(self):
        """Complex scenario where both calendars changed all events."""
        base_event = CalendarEvent.create({
            "uid": "1",
            "summary": "Base",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        prev_cal = Calendar(events=[base_event])

        mod1 = CalendarEvent.create({"uid": "1", "summary": "Modified by cal1",
            "start": base_event.DTSTART, "end": base_event.DTEND})
        mod2 = CalendarEvent.create({"uid": "1", "summary": "Modified by cal2",
            "start": base_event.DTSTART, "end": base_event.DTEND})
        curr_cal1 = Calendar(events=[mod1])
        curr_cal2 = Calendar(events=[mod2])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 2
        assert len(updated2.events) == 2
        assert updated1 == updated2

    def test_conflict_modify_separate_fields(self):
        """Conflict: modify different fields on each side - merge into single event."""
        base_event = CalendarEvent.create({
            "uid": "1",
            "summary": "Base",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
            "description": "",
        })
        prev_cal = Calendar(events=[base_event])

        event1 = CalendarEvent.create({"uid": "1", "summary": "New Summary",
            "start": base_event.DTSTART, "end": base_event.DTEND,
            "description": ""})
        event2 = CalendarEvent.create({"uid": "1", "summary": "Base",
            "start": base_event.DTSTART, "end": base_event.DTEND,
            "description": "", "location": "Office"})
        curr_cal1 = Calendar(events=[event1])
        curr_cal2 = Calendar(events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 1
        assert len(updated2.events) == 1
        assert updated1 == updated2
        merged = updated1.events[0]
        assert merged.summary == "New Summary"
        assert merged.location == "Office"


class TestSyncWithFilters:
    """Test synchronization with filters."""

    def test_sync_with_future_filter(self):
        """Sync with future filter works."""
        from syncalpy.filters.future_only import FutureOnlyFilter

        past_event = CalendarEvent.create({
            "uid": "1",
            "summary": "Past Event",
            "start": datetime.now() + timedelta(days=-1),
            "end": datetime.now() + timedelta(days=-1, hours=1),
        })
        future_event = CalendarEvent.create({
            "uid": "2",
            "summary": "Future Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })

        prev_cal = Calendar(events=[])

        curr_cal1 = Calendar(
            events=[past_event, future_event]
        )
        curr_cal2 = Calendar(events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2,
            filters1=[{"name": "future_only"}]
        )

        assert updated2.get_event_by_uid("2") is not None
        assert len(updated2.events) == 1

    def test_sync_with_regexp_filter(self):
        """Sync respects regexp_summary filter."""
        event1 = CalendarEvent.create({
            "uid": "1",
            "summary": "WORK Meeting",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        event2 = CalendarEvent.create({
            "uid": "2",
            "summary": "PRIVATE Lunch",
            "start": datetime.now() + timedelta(days=2),
            "end": datetime.now() + timedelta(days=2, hours=1),
        })

        prev_cal = Calendar(events=[])

        curr_cal1 = Calendar(
            events=[event1, event2]
        )
        curr_cal2 = Calendar(events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2,
            filters1=[{"name": "regexp_summary", "pattern": "WORK"}]
        )

        assert len(updated2.events) == 1
        assert updated2.get_event_by_uid("1") is not None
 

class TestEdgeCases:
    """Test edge cases."""

    def test_empty_calendars(self):
        """Empty calendars sync correctly."""
        prev_cal = Calendar(events=[])
        curr_cal1 = Calendar(events=[])
        curr_cal2 = Calendar(events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 0
        assert len(updated2.events) == 0

    def test_events_without_uid(self):
        """Events without UID are handled - set_missing_uids generates UID."""
        event = CalendarEvent.create({"uid": "",
            "summary": "Event without UID",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1)})
        prev_cal = Calendar(events=[])

        curr_cal1 = Calendar(events=[event])
        curr_cal2 = Calendar(events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated2.events) == 1
        assert updated1 == updated2

    def test_preserve_existing_events(self):
        """Existing events are preserved during sync."""
        event1 = CalendarEvent.create({
            "uid": "1",
            "summary": "Existing Event",
            "start": datetime.now() + timedelta(days=1),
            "end": datetime.now() + timedelta(days=1, hours=1),
        })
        event2 = CalendarEvent.create({
            "uid": "2",
            "summary": "New Event",
            "start": datetime.now() + timedelta(days=2),
            "end": datetime.now() + timedelta(days=2, hours=1),
        })

        prev_cal = Calendar(events=[event1])

        curr_cal1 = Calendar(events=[event1, event2])
        curr_cal2 = Calendar(events=[event1])

        updated1, updated2 = synchronize_calendars(
            prev_cal, curr_cal1, curr_cal2
        )

        assert len(updated2.events) == 2
        assert updated1 == updated2
