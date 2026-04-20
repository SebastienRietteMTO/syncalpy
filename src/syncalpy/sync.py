"""Main synchronization logic."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from .calendar import Calendar
from .event import CalendarEvent
from .config import Config, apply_filters, create_protocol, load_calendar_config


def load_state(state_dir: Path, name: str) -> Calendar:
    """Load calendar state from state directory."""
    state_file = state_dir / f"{name}.json"
    if not state_file.exists():
        return Calendar(name=name)

    with open(state_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = []
    for event_data in data.get("events", []):
        event = CalendarEvent(
            uid=event_data["uid"],
            summary=event_data["summary"],
            start=datetime.fromisoformat(event_data["start"]) if event_data.get("start") else None,
            end=datetime.fromisoformat(event_data["end"]) if event_data.get("end") else None,
            description=event_data.get("description"),
            location=event_data.get("location"),
            source=event_data.get("source", ""),
        )
        events.append(event)

    calendar = Calendar(name=name, events=events)
    return calendar


def save_state(state_dir: Path, calendar: Calendar) -> None:
    """Save calendar state to state directory."""
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f"{calendar.name}.json"

    events = []
    for event in calendar.events:
        events.append({
            "uid": event.uid,
            "summary": event.summary,
            "start": event.start.isoformat() if event.start else None,
            "end": event.end.isoformat() if event.end else None,
            "description": event.description,
            "source": event.source,
        })

    data = {"events": events}

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def synchronize_calendars(
    prev_cal1: Calendar,
    prev_cal2: Calendar,
    curr_cal1: Calendar,
    curr_cal2: Calendar,
) -> Tuple[Calendar, Calendar]:
    """Synchronize two calendars bidirectionally.

    Returns the updated calendars after synchronization.
    In case of conflict, keeps both versions (prudent approach).

    Args:
        prev_cal1: Previous state of calendar 1
        prev_cal2: Previous state of calendar 2
        curr_cal1: Current state of calendar 1
        curr_cal2: Current state of calendar 2

    Returns:
        Tuple of updated calendars
    """
    diff_1 = curr_cal1.diff(prev_cal1)
    diff_2 = curr_cal2.diff(prev_cal2)

    updated_cal1 = Calendar(
        name=curr_cal1.name,
        events=list(curr_cal1.events),
        url=curr_cal1.url,
        protocol=curr_cal1.protocol,
    )
    updated_cal2 = Calendar(
        name=curr_cal2.name,
        events=list(curr_cal2.events),
        url=curr_cal2.url,
        protocol=curr_cal2.protocol,
    )

    for event in diff_1["added"]:
        existing = updated_cal2.get_event_by_uid(event.uid)
        if not existing:
            new_event = CalendarEvent(
                uid=event.uid,
                summary=event.summary,
                start=event.start,
                end=event.end,
                description=event.description,
                location=event.location,
                source=updated_cal2.name,
            )
            updated_cal2.add_event(new_event)

    for event in diff_2["added"]:
        existing = updated_cal1.get_event_by_uid(event.uid)
        if not existing:
            new_event = CalendarEvent(
                uid=event.uid,
                summary=event.summary,
                start=event.start,
                end=event.end,
                description=event.description,
                location=event.location,
                source=updated_cal1.name,
            )
            updated_cal1.add_event(new_event)

    for event in diff_1["removed"]:
        changed_uids = {e.uid for e in diff_2["added"]}
        changed_uids |= {pair[0].uid for pair in diff_2["modified"]}
        changed_uids |= {pair[1].uid for pair in diff_2["modified"]}
        if event.uid in changed_uids:
            continue
        existing = updated_cal2.get_event_by_uid(event.uid)
        if existing:
            updated_cal2.remove_event(event.uid)

    for event in diff_2["removed"]:
        changed_uids = {e.uid for e in diff_1["added"]}
        changed_uids |= {pair[0].uid for pair in diff_1["modified"]}
        changed_uids |= {pair[1].uid for pair in diff_1["modified"]}
        if event.uid in changed_uids:
            continue
        existing = updated_cal1.get_event_by_uid(event.uid)
        if existing:
            updated_cal1.remove_event(event.uid)

    for event_pair in diff_1["modified"]:
        new_event = event_pair[0]
        existing = updated_cal2.get_event_by_uid(new_event.uid)
        if existing and not Calendar.events_equal(existing, new_event):
            conflict_event = CalendarEvent(
                uid=f"{new_event.uid}_conflict",
                summary=f"[CONFLICT] {new_event.summary}",
                start=new_event.start,
                end=new_event.end,
                description=f"Original: {existing.description}\nModified: {new_event.description}",
                location=new_event.location,
                source=updated_cal2.name,
            )
            updated_cal2.add_event(conflict_event)
        elif not existing:
            new_event_copy = CalendarEvent(
                uid=new_event.uid,
                summary=new_event.summary,
                start=new_event.start,
                end=new_event.end,
                description=new_event.description,
                location=new_event.location,
                source=updated_cal2.name,
            )
            updated_cal2.add_event(new_event_copy)

    for event_pair in diff_2["modified"]:
        new_event = event_pair[0]
        existing = updated_cal1.get_event_by_uid(new_event.uid)
        if existing and not Calendar.events_equal(existing, new_event):
            conflict_event = CalendarEvent(
                uid=f"{new_event.uid}_conflict",
                summary=f"[CONFLICT] {new_event.summary}",
                start=new_event.start,
                end=new_event.end,
                description=f"Original: {existing.description}\nModified: {new_event.description}",
                location=new_event.location,
                source=updated_cal1.name,
            )
            updated_cal1.add_event(conflict_event)
        elif not existing:
            new_event_copy = CalendarEvent(
                uid=new_event.uid,
                summary=new_event.summary,
                start=new_event.start,
                end=new_event.end,
                description=new_event.description,
                location=new_event.location,
                source=updated_cal1.name,
            )
            updated_cal1.add_event(new_event_copy)

    return updated_cal1, updated_cal2


def run_synchronization(sync_config: Dict[str, Any], config: Config) -> None:
    """Run a single synchronization."""
    state_dir = config.get_state_dir()

    cal1_config = sync_config.get("calendar1", {})
    cal2_config = sync_config.get("calendar2", {})

    cal1_name = cal1_config.get("name", "calendar1")
    cal2_name = cal2_config.get("name", "calendar2")

    cal1 = load_calendar_config(cal1_config)
    cal2 = load_calendar_config(cal2_config)

    protocol1 = create_protocol(cal1)
    protocol2 = create_protocol(cal2)

    print(f"Fetching {cal1_name}...")
    curr_cal1 = protocol1.fetch()
    curr_cal1.name = cal1_name
    curr_cal1 = apply_filters(curr_cal1)

    print(f"Fetching {cal2_name}...")
    curr_cal2 = protocol2.fetch()
    curr_cal2.name = cal2_name
    curr_cal2 = apply_filters(curr_cal2)

    print(f"Loading previous state for {cal1_name}...")
    prev_cal1 = load_state(state_dir, cal1_name)

    print(f"Loading previous state for {cal2_name}...")
    prev_cal2 = load_state(state_dir, cal2_name)

    print(f"Synchronizing {cal1_name} <-> {cal2_name}...")
    updated_cal1, updated_cal2 = synchronize_calendars(
        prev_cal1, prev_cal2, curr_cal1, curr_cal2
    )

    print(f"Pushing changes to {cal1_name}...")
    updated_cal1.url = curr_cal1.url
    updated_cal1.protocol = curr_cal1.protocol
    try:
        protocol1_push = create_protocol(updated_cal1)
        protocol1_push.push(updated_cal1)
    except (RuntimeError, OSError) as e:
        print(f"Warning: Failed to push to {cal1_name}: {e}")

    print(f"Pushing changes to {cal2_name}...")
    updated_cal2.url = curr_cal2.url
    updated_cal2.protocol = curr_cal2.protocol
    try:
        protocol2_push = create_protocol(updated_cal2)
        protocol2_push.push(updated_cal2)
    except (RuntimeError, OSError) as e:
        print(f"Warning: Failed to push to {cal2_name}: {e}")

    print(f"Saving state for {cal1_name}...")
    save_state(state_dir, curr_cal1)

    print(f"Saving state for {cal2_name}...")
    save_state(state_dir, curr_cal2)

    print("Synchronization complete.")
