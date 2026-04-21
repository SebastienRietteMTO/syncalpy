# AGENTS.md - Syncalpy

This file provides instructions for agents working on this codebase.

## Project Overview

Syncalpy is a Python package for synchronizing multiple calendars. It supports:
- Multiple sync protocols: CalDAV, local ICS files, Zimbra
- Filters: future-only, regexp matching
- Conflict resolution: keeps both versions in case of conflict

## Development Commands

### Install in development mode
```bash
pip install -e .
```

### Run tests
```bash
pytest tests/
```

### Run tests with coverage
```bash
pytest tests/ --cov=syncalpy --cov-report=html
```

### Run CLI
```bash
syncalpy --help
syncalpy sync
syncalpy list
syncalpy status
```

## Configuration

User configuration is stored in `~/.syncalpy/config.yaml`:

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
        - name: "regexp_summary"
          pattern: "work|meeting"
    calendar2:
      name: "home"
      protocol: "ics_file"
      url: "/path/to/calendar.ics"
      filters: []
```

## Project Structure

```
src/syncalpy/
├── __init__.py          # Package init
├── __main__.py          # CLI entry point
├── config.py            # Configuration management
├── sync.py              # Main synchronization logic
├── calendar.py         # Calendar model
├── event.py             # Event model
├── filters/             # Filter implementations
│   ├── future_only.py
│   └── regexp.py
└── protocols/           # Protocol implementations
    ├── caldav.py
    ├── ics_file.py
    └── zimbra.py
```

## Testing

- Unit tests: `tests/unit/`
- Scenario tests: `tests/scenarios/`
- Run all: `pytest tests/`

## License

CeCILL-C - See LICENSE
