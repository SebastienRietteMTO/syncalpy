# Configuration

Create a configuration file at `~/.syncalpy/config.yaml`:

```yaml
synchronizations:
  - name: "my-sync"
    calendar1:
      name: "work"
      protocol: "caldav"
      url: "https://caldav.example.com/calendar"
      user: "user"
      password: "password"
      filters:
        - name: "future_only"
        - name: "regexp"
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

## Filters

### Future Only

```yaml
filters:
  - name: "future_only"
```

### Regexp

```yaml
filters:
  - name: "regexp"
    pattern: "work|meeting"
    field: "title"  # optional: title, description, any
```
