"""Main synchronization logic."""

import netrc
from pathlib import Path
from typing import Any, Dict

from .calendar import Calendar
from .event import CalendarEvent
from .protocols.ics_file import ICSFileProtocol
from .protocols import get_protocol


class Synchronization:
    """Represents a single synchronization configuration."""

    def __init__(self, sync_config: Dict[str, Any], state_dir: str):
        """Initialize synchronization.

        Args:
            sync_config: Synchronization configuration dict
            state_dir: Path to state directory
        """
        self._config = sync_config
        self._state_dir = state_dir
        self.cal1_config = sync_config.get("calendar1", {})
        self.cal2_config = sync_config.get("calendar2", {})

    @property
    def name(self) -> str:
        """Get synchronization name."""
        return self._config.get("name", "sync")

    @property
    def cal1_name(self) -> str:
        """Get calendar 1 name."""
        return self.cal1_config.get("name", "calendar1")

    @property
    def cal2_name(self) -> str:
        """Get calendar 2 name."""
        return self.cal2_config.get("name", "calendar2")

    @property
    def sync_mode(self) -> str:
        """Get sync mode."""
        return self._config.get("sync_mode", "bidirectional")

    def _resolve_password(self, password: str, cal_url: str, username: str) -> str:
        """Resolve password, supporting NETRC special value.

        If password is 'NETRC', read credentials from ~/.netrc file
        using the hostname from the calendar URL.
        """
        if password != "NETRC":
            return password

        try:
            from urllib.parse import urlparse
            netrc_path = Path.home() / ".netrc"
            if not netrc_path.exists():
                netrc_path = Path.home() / "_netrc"

            if netrc_path.exists():
                hostname = ""
                if cal_url:
                    parsed = urlparse(cal_url)
                    hostname = parsed.hostname or ""

                if hostname:
                    auth = netrc.netrc(str(netrc_path))
                    auth_entry = auth.authenticators(hostname)
                    if auth_entry:
                        login, _, netrc_password = auth_entry
                        if username and login != username:
                            return password
                        if netrc_password:
                            return netrc_password
        except Exception:
            pass

        return password

    def _load_calendar(self, cal_config: Dict[str, Any], name: str) -> Calendar:
        """Load and create Calendar from config dict."""
        username = cal_config.get("user", "")
        password = cal_config.get("password", "")
        cal_url = cal_config.get("url", "")
        password = self._resolve_password(password, cal_url, username)

        protocol_class = get_protocol(cal_config.get("protocol", "ics_file"))
        calendar = protocol_class(
            url=cal_url,
            username=username,
            password=password,
        )
        calendar.set_missing_uids()
        return calendar

    def get_cal1(self) -> Calendar:
        """Get calendar 1 with filters applied."""
        cal1 = self._load_calendar(self.cal1_config, self.cal1_name)
        return cal1.apply_filters(self.cal1_config.get("filters", []))

    def get_cal2(self) -> Calendar:
        """Get calendar 2 with filters applied."""
        cal2 = self._load_calendar(self.cal2_config, self.cal2_name)
        return cal2.apply_filters(self.cal2_config.get("filters", []))

    def get_state_calendar(self) -> ICSFileProtocol:
        """Get the state calendar for this synchronization."""
        return ICSFileProtocol(f"{self._state_dir}/{self.name}.ics")

    @staticmethod
    def synchronize(cal1, cal2, ref, sync_mode):
        """Run the synchronization"""

        if sync_mode == "cal2_to_cal1":
            cal1, cal2 = cal2, cal1

        diff_1 = cal1.diff(ref)
        diff_2 = cal2.diff(ref)

        for uid in diff_1['removed']:
            # Removed uid in cal1
            if sync_mode != "bidirectional" or uid not in diff_2['changed']:
                # If not bidirectional, cal2 is a copy
                # If bidirectional and uid has not changed in cal2, we delete in cal2
                # uid can have been also deleted in cal2
                cal2.remove_event(uid)
                ref.remove_event(uid)
                diff_2['removed'] = [u for u in diff_2['removed'] if u != uid]
            else:
                # We deleted from cal1 but there's un update in cal2
                # We keep the cal2 version everywhere
                event_in_cal2 = cal2.select_events_by_uid(uid)
                cal1.add_event(event_in_cal2)
                ref.add_event(event_in_cal2)
                diff_2['changed'] = [u for u in diff_2['changed'] if u != uid]

        for uid in diff_1['changed']:
            # Modified uid in cal1
            if sync_mode != "bidirectional" or uid not in diff_2['changed']:
                # If not bidirectional, cal2 is a copy
                # If bidirectional and uid has not changed in cal2, we copy
                # uid can have been deleted in cal2
                event_in_cal1 = cal1.select_events_by_uid(uid)
                cal2.add_event(event_in_cal1)
                ref.add_event(event_in_cal1)
                diff_2['removed'] = [u for u in diff_2['removed'] if u != uid]
            else:
                # Modified in both versions
                # There is a conflict, we push both versions in cal1 and cal2
                e = ref.select_events_by_uid(uid)
                e1 = cal1.select_events_by_uid(uid)
                e2 = cal2.select_events_by_uid(uid)
                for event in Synchronization._conflict(e, e1, e2):
                    cal1.add_event(event)
                    cal2.add_event(event)
                    ref.add_event(event)
                diff_2['changed'] = [u for u in diff_2['changed'] if u != uid]

        if sync_mode == "bidirectional":
            # All conflicts has been solved
            for uid in diff_2['removed']:
                cal1.remove_event(uid)
                ref.remove_event(uid)
            for uid in diff_2['changed']:
                event_in_cal2 = cal2.select_events_by_uid(uid)
                cal1.add_event(event_in_cal2)
                ref.add_event(event_in_cal2)

    @staticmethod
    def _conflict(base, cal1, cal2):

        if cal1 == cal2:
            # Added or modified on both sides, but the same way
            # We return one to update ref
            return [cal1]

        # We must associate events in all calendars
        def categorize(cal):
            master_candidates = [event for event in cal.events if 'RRULE' in event]
            if len(master_candidates) == 0:
                if len(cal.events) == 1:
                    master_candidates = [cal.events[0]]
                else:
                    raise ValueError("No RRULE event found and multiple events exist")
            elif len(master_candidates) > 1:
                raise ValueError("Multiple events with RRULE found")
            master = master_candidates[0]
            other = {}
            for event in [event for event in cal.events if event != master]:
                key = (event.start, event.end)
                if key in other:
                    raise ValueError("Multiple modifications for same occurrence")
                other[key] = event
            return master, other
        masterbase, otherbase = categorize(base)
        master1, other1 = categorize(cal1)
        master2, other2 = categorize(cal2)
        associated=[(masterbase, master1, master2)]
        for key in set(list(otherbase.keys()) + list(other1.keys()) + list(other2.keys())):
            associated.append((otherbase.get(key, None),
                               other1.get(key, None),
                               other2.get(key, None)))

        # Comparison function
        def compare(eventbase, event1, event2):
            if eventbase is None:
                eventbase = dict()
            all_keys = set(event1.keys()) | set(event2.keys()) | set(eventbase.keys())
            fields = [k for k in all_keys if k not in CalendarEvent.ignore_keys_eq]
            changed1 = [f for f in fields if event1.get(f) != eventbase.get(f)]
            changed2 = [f for f in fields if event2.get(f) != eventbase.get(f)]
            return changed1, changed2

        # Comparison to detect non-mergeable events
        mergeable = True
        for eventbase, event1, event2 in associated:
            if eventbase is None and event1 != event2:
                mergeable = False
            elif event1 == event2:
                pass
            elif event1 is not None and event2 is not None:
                changed1, changed2 = compare(eventbase, event1, event2)
                if set(changed1) & set(changed2):
                    mergeable = False

        if mergeable:
            # Merge
            for eventbase, event1, event2 in associated:
                if event1 is None:
                    cal1.add_event(event2)
                elif event2 is None:
                    cal2.add_event(event1)
                elif event1 == event2:
                    pass
                else:
                    changed1, changed2 = compare(eventbase, event1, event2)
                    for field in changed2:
                        event1[field] = event2.get(field)
            return [cal1]

        # Duplicate
        uid = None
        for event in cal2.events:
            if uid is None:
                event.set_uid()
                uid = event.uid
            else:
                event.set_uid(uid)
            event.conflict()
        for event in cal1.events:
            event.conflict()
        return [cal1, cal2]

    def run(self) -> None:
        """Run the synchronization."""
        with self.get_cal1() as cal1, self.get_cal2() as cal2, self.get_state_calendar() as ref:
            self.synchronize(cal1, cal2, ref, self.sync_mode)
