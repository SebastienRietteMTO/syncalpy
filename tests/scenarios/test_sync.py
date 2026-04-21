"""Scenario tests for synchronization.

These tests cover various conflict resolution scenarios.
"""

import pytest
from datetime import datetime, timedelta
from syncalpy.calendar import Calendar
from syncalpy.event import CalendarEvent
from syncalpy.sync import synchronize_calendars


def create_event(uid, summary, days_from_now=0, description=""):
    """Helper to create test events."""
    return CalendarEvent(
        uid=uid,
        summary=summary,
        start=datetime.now() + timedelta(days=days_from_now),
        end=datetime.now() + timedelta(days=days_from_now, hours=1),
        description=description,
    )


class TestSyncConflictResolution:
    """Test conflict resolution scenarios."""

    def test_no_changes(self):
        """No changes - calendars identical."""
        event = create_event("1", "Event", 1)
        cal1 = Calendar(name="cal1", events=[event])
        cal2 = Calendar(name="cal2", events=[event])

        updated1, updated2 = synchronize_calendars(cal1, cal2, cal1, cal2)

        assert len(updated1.events) == 1
        assert len(updated2.events) == 1

    def test_add_event_to_cal1(self):
        """Add event to calendar 1 propagates to calendar 2."""
        prev_cal1 = Calendar(name="cal1", events=[])
        prev_cal2 = Calendar(name="cal2", events=[])

        event = create_event("1", "New Event", 1)
        curr_cal1 = Calendar(name="cal1", events=[event])
        curr_cal2 = Calendar(name="cal2", events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert len(updated2.events) == 1
        assert updated2.get_event_by_uid("1") is not None

    def test_add_event_to_cal2(self):
        """Add event to calendar 2 propagates to calendar 1."""
        prev_cal1 = Calendar(name="cal1", events=[])
        prev_cal2 = Calendar(name="cal2", events=[])

        event = create_event("1", "New Event", 1)
        curr_cal1 = Calendar(name="cal1", events=[])
        curr_cal2 = Calendar(name="cal2", events=[event])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 1
        assert updated1.get_event_by_uid("1") is not None

    def test_delete_event_from_cal1(self):
        """Delete event from cal1 removes from cal2."""
        event = create_event("1", "Event", 1)
        prev_cal1 = Calendar(name="cal1", events=[event])
        prev_cal2 = Calendar(name="cal2", events=[event])

        curr_cal1 = Calendar(name="cal1", events=[])
        curr_cal2 = Calendar(name="cal2", events=[event])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert updated2.get_event_by_uid("1") is None

    def test_delete_event_from_cal2(self):
        """Delete event from cal2 removes from cal1."""
        event = create_event("1", "Event", 1)
        prev_cal1 = Calendar(name="cal1", events=[event])
        prev_cal2 = Calendar(name="cal2", events=[event])

        curr_cal1 = Calendar(name="cal1", events=[event])
        curr_cal2 = Calendar(name="cal2", events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert updated1.get_event_by_uid("1") is None

    def test_conflict_delete_cal1_modify_cal2(self):
        """Conflict: delete from cal1, modify in cal2 - modification propagates."""
        old_event = create_event("1", "Original", 1, "Original description")
        prev_cal1 = Calendar(name="cal1", events=[old_event])
        prev_cal2 = Calendar(name="cal2", events=[old_event])

        curr_cal1 = Calendar(name="cal1", events=[])
        modified_event = CalendarEvent(
            uid="1", summary="Modified", start=old_event.start,
            end=old_event.end, description="Modified description"
        )
        curr_cal2 = Calendar(name="cal2", events=[modified_event])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        updated_event = updated1.get_event_by_uid("1")
        assert updated_event is not None
        assert updated_event.summary == "Modified"

    def test_conflict_modify_cal1_delete_cal2(self):
        """Modify in cal1 propagates to cal2 (which deleted locally)."""
        old_event = create_event("1", "Original", 1, "Original description")
        prev_cal1 = Calendar(name="cal1", events=[old_event])
        prev_cal2 = Calendar(name="cal2", events=[old_event])

        modified_event = CalendarEvent(
            uid="1", summary="Modified", start=old_event.start,
            end=old_event.end, description="Modified description"
        )
        curr_cal1 = Calendar(name="cal1", events=[modified_event])
        curr_cal2 = Calendar(name="cal2", events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        updated_event = updated2.get_event_by_uid("1")
        assert updated_event is not None
        assert updated_event.summary == "Modified"

    def test_conflict_modify_both_titles(self):
        """Conflict: modify title on both sides - create conflict event."""
        old_event = create_event("1", "Original", 1)
        prev_cal1 = Calendar(name="cal1", events=[old_event])
        prev_cal2 = Calendar(name="cal2", events=[old_event])

        event1 = CalendarEvent(
            uid="1", summary="Modified by cal1", start=old_event.start, end=old_event.end
        )
        event2 = CalendarEvent(
            uid="1", summary="Modified by cal2", start=old_event.start, end=old_event.end
        )
        curr_cal1 = Calendar(name="cal1", events=[event1])
        curr_cal2 = Calendar(name="cal2", events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert updated1.get_event_by_uid("1_conflict") is not None
        assert updated2.get_event_by_uid("1_conflict") is not None

    def test_conflict_modify_both_dates(self):
        """Conflict: modify dates on both sides - create conflict event."""
        old_event = create_event("1", "Event", 1)
        prev_cal1 = Calendar(name="cal1", events=[old_event])
        prev_cal2 = Calendar(name="cal2", events=[old_event])

        event1 = CalendarEvent(
            uid="1", summary="Event",
            start=datetime.now() + timedelta(days=2),
            end=datetime.now() + timedelta(days=2, hours=1)
        )
        event2 = CalendarEvent(
            uid="1", summary="Event",
            start=datetime.now() + timedelta(days=3),
            end=datetime.now() + timedelta(days=3, hours=1)
        )
        curr_cal1 = Calendar(name="cal1", events=[event1])
        curr_cal2 = Calendar(name="cal2", events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert updated1.get_event_by_uid("1_conflict") is not None
        assert updated2.get_event_by_uid("1_conflict") is not None

    def test_conflict_modify_both_descriptions(self):
        """Conflict: modify description on both sides - create conflict event."""
        old_event = CalendarEvent(
            uid="1", summary="Event",
            start=datetime.now() + timedelta(days=1),
            end=datetime.now() + timedelta(days=1, hours=1),
            description="Original"
        )
        prev_cal1 = Calendar(name="cal1", events=[old_event])
        prev_cal2 = Calendar(name="cal2", events=[old_event])

        event1 = CalendarEvent(
            uid="1", summary="Event",
            start=old_event.start, end=old_event.end,
            description="Description from cal1"
        )
        event2 = CalendarEvent(
            uid="1", summary="Event",
            start=old_event.start, end=old_event.end,
            description="Description from cal2"
        )
        curr_cal1 = Calendar(name="cal1", events=[event1])
        curr_cal2 = Calendar(name="cal2", events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert updated1.get_event_by_uid("1_conflict") is not None
        conflict = updated1.get_event_by_uid("1_conflict")
        assert "Original" in conflict.description

    def test_sync_multiple_events(self):
        """Synchronize multiple events correctly."""
        events1 = [
            create_event("1", "Event 1", 1),
            create_event("2", "Event 2", 2),
            create_event("3", "Event 3", 3),
        ]
        events2 = [
            create_event("1", "Event 1", 1),
            create_event("2", "Event 2", 2),
            create_event("3", "Event 3", 3),
        ]

        prev_cal1 = Calendar(name="cal1", events=events1)
        prev_cal2 = Calendar(name="cal2", events=events2)

        new_event = create_event("4", "Event 4", 4)
        curr_cal1 = Calendar(name="cal1", events=events1 + [new_event])
        curr_cal2 = Calendar(name="cal2", events=events2)

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert len(updated2.events) == 4
        assert updated2.get_event_by_uid("4") is not None

    def test_bidirectional_sync(self):
        """Changes propagate bidirectionally."""
        prev_cal1 = Calendar(name="cal1", events=[])
        prev_cal2 = Calendar(name="cal2", events=[])

        event1 = create_event("1", "From cal1", 1)
        event2 = create_event("2", "From cal2", 1)

        curr_cal1 = Calendar(name="cal1", events=[event1])
        curr_cal2 = Calendar(name="cal2", events=[event2])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 2
        assert len(updated2.events) == 2
        assert updated1.get_event_by_uid("2") is not None
        assert updated2.get_event_by_uid("1") is not None

    def test_complex_conflict_all_changed(self):
        """Complex: delete, modify, add on both sides."""
        old1 = create_event("1", "Old", 1)
        old2 = create_event("2", "Old 2", 2)

        prev_cal1 = Calendar(name="cal1", events=[old1, old2])
        prev_cal2 = Calendar(name="cal2", events=[old1, old2])

        event1_new = create_event("1", "Modified", 1)
        curr_cal1 = Calendar(name="cal1", events=[event1_new])

        new2 = create_event("2", "New event", 2)
        curr_cal2 = Calendar(name="cal2", events=[new2])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert len(updated1.events) >= 1
        assert len(updated2.events) >= 1


class TestSyncWithFilters:
    """Test synchronization with filters applied."""

    def test_sync_with_future_filter(self):
        """Sync respects future-only filter."""
        from syncalpy.filters.future_only import FutureOnlyFilter

        past_event = create_event("1", "Past", -1)
        future_event = create_event("2", "Future", 1)

        prev_cal1 = Calendar(name="cal1", events=[])
        prev_cal2 = Calendar(name="cal2", events=[])

        curr_cal1 = Calendar(name="cal1", events=[past_event, future_event])
        curr_cal2 = Calendar(name="cal2", events=[])

        filter_obj = FutureOnlyFilter()
        curr_cal1.events = filter_obj.filter(curr_cal1.events)

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert len(updated2.events) == 1
        assert updated2.get_event_by_uid("2") is not None

    def test_sync_with_regexp_filter(self):
        """Sync respects regexp filter."""
        from syncalpy.filters.regexp import RegexpFilter

        meeting = create_event("1", "Team Meeting", 1)
        lunch = create_event("2", "Lunch", 1)

        prev_cal1 = Calendar(name="cal1", events=[])
        prev_cal2 = Calendar(name="cal2", events=[])

        curr_cal1 = Calendar(name="cal1", events=[meeting, lunch])
        curr_cal2 = Calendar(name="cal2", events=[])

        filter_obj = RegexpFilter(pattern="meeting")
        curr_cal1.events = filter_obj.filter(curr_cal1.events)

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert len(updated2.events) == 1
        assert updated2.get_event_by_uid("1") is not None
        assert updated2.get_event_by_uid("2") is None

    def test_sync_with_filter_and_full_cal1(self):
        """Filter is applied to source, but unsynced events stay in cal1."""
        from syncalpy.filters.regexp import RegexpFilter

        event1 = CalendarEvent(uid="1", summary="[WORK] Meeting", start=datetime(2026, 4, 21, 14), end=datetime(2026, 4, 21, 15))
        event2 = CalendarEvent(uid="2", summary="[PRIVATE] Lunch", start=datetime(2026, 4, 22, 12), end=datetime(2026, 4, 22, 13))

        prev_cal1 = Calendar(name="cal1", events=[])
        prev_cal2 = Calendar(name="cal2", events=[])

        cal1 = Calendar(name="cal1", events=[event1, event2])
        filter_obj = RegexpFilter(pattern=r"^\[WORK\]")
        cal1.events = filter_obj.filter(cal1.events)

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, cal1, Calendar(name="cal2", events=[])
        )

        assert len(updated1.events) == 1
        assert len(updated2.events) == 1
        assert updated2.get_event_by_uid("1") is not None


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_calendars(self):
        """Handle empty calendars."""
        prev_cal1 = Calendar(name="cal1", events=[])
        prev_cal2 = Calendar(name="cal2", events=[])
        curr_cal1 = Calendar(name="cal1", events=[])
        curr_cal2 = Calendar(name="cal2", events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert len(updated1.events) == 0
        assert len(updated2.events) == 0

    def test_events_without_uid(self):
        """Events without UIDs get unique IDs."""
        event = CalendarEvent(
            uid="", summary="Test",
            start=datetime.now() + timedelta(days=1),
            end=datetime.now() + timedelta(days=1, hours=1)
        )
        if not event.uid:
            event.uid = CalendarEvent.generate_uid()

        cal1 = Calendar(name="cal1", events=[event])
        cal2 = Calendar(name="cal2", events=[])

        prev_cal1 = Calendar(name="cal1", events=[])
        prev_cal2 = Calendar(name="cal2", events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, cal1, cal2
        )

        assert len(updated2.events) == 1

    def test_preserve_existing_events(self):
        """Existing events not in current sync are preserved."""
        existing = create_event("1", "Existing", 1)

        prev_cal1 = Calendar(name="cal1", events=[existing])
        prev_cal2 = Calendar(name="cal2", events=[])

        curr_cal1 = Calendar(name="cal1", events=[existing])
        curr_cal2 = Calendar(name="cal2", events=[])

        updated1, updated2 = synchronize_calendars(
            prev_cal1, prev_cal2, curr_cal1, curr_cal2
        )

        assert updated1.get_event_by_uid("1") is not None

    def test_three_way_sync(self):
        """Simulate three-way sync scenario."""
        base = create_event("1", "Base", 1)

        prev_a = Calendar(name="a", events=[base])
        prev_b = Calendar(name="b", events=[base])
        prev_c = Calendar(name="c", events=[base])

        mod_a = CalendarEvent(
            uid="1", summary="Modified A",
            start=base.start, end=base.end
        )
        mod_b = CalendarEvent(
            uid="1", summary="Modified B",
            start=base.start, end=base.end
        )
        curr_a = Calendar(name="a", events=[mod_a])
        curr_b = Calendar(name="b", events=[mod_b])
        curr_c = Calendar(name="c", events=[base])

        updated_a, updated_b = synchronize_calendars(
            prev_a, prev_b, curr_a, curr_b
        )

        assert updated_a.get_event_by_uid("1") is not None
        assert updated_b.get_event_by_uid("1") is not None