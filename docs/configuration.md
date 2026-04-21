# Configuration

Create a configuration file at `~/.syncalpy/config.yaml`:

```yaml
synchronizations:
  - name: "my-sync"
    sync_mode: "bidirectional"  # bidirectional, cal1_to_cal2, cal2_to_cal1
    calendar1:
      name: "work"
      protocol: "caldav"
      url: "https://caldav.example.com/calendar"
      user: "user"
      password: "password"
      filters:
        - name: "future_only"
        - name: "regexp_summary"
          pattern: "work|meeting"
    calendar2:
      name: "home"
      protocol: "ics_file"
      url: "/path/to/calendar.ics"
      filters: []
```

## Calendar Options

Each calendar supports:

- `name`: Calendar name
- `protocol`: Protocol type (caldav, ics_file, zimbra)
- `url`: Calendar URL or file path
- `user`: Username (for CalDAV/Zimbra)
- `password`: Password (for CalDAV/Zimbra)
- `filters`: List of filters to apply

## Sync Mode

- `bidirectional`: Sync events in both directions (default)
- `cal1_to_cal2`: Only sync from calendar1 to calendar2
- `cal2_to_cal1`: Only sync from calendar2 to calendar1

## Filters

### Future Only

```yaml
filters:
  - name: "future_only"
```

### Regexp Summary

```yaml
filters:
  - name: "regexp_summary"
    pattern: "work|meeting"
```

### Regexp Description

```yaml
filters:
  - name: "regexp_description"
    pattern: "important|urgent"
```

### Regexp Location

```yaml
filters:
  - name: "regexp_location"
    pattern: "conference|room"
```
