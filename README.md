# Syncalpy

Calendar synchronization tool for Python.

## Overview

Syncalpy is a Python package that allows you to synchronize multiple calendars. It supports various protocols including CalDAV, local ICS files, and Zimbra.

## Features

- Synchronize between multiple calendar sources
- Support for CalDAV, ICS files, and Zimbra protocols
- Apply filters (future-only, regexp matching)
- Conflict resolution (keeps both versions)
- Command-line interface

## Installation

```bash
pip install syncalpy
```

## Configuration

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
    calendar2:
      name: "home"
      protocol: "ics_file"
      url: "/path/to/calendar.ics"
      filters: []
```

## Usage

```bash
# Run synchronization
syncalpy sync

# List configured synchronizations
syncalpy list

# Show status
syncalpy status
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=syncalpy --cov-report=html
```

## License

This software is under the CeCILL-C license. See LICENSE for details.
