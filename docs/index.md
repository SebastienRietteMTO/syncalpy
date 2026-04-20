# Syncalpy

Calendar synchronization tool for Python.

## Overview

Syncalpy allows you to synchronize multiple calendars using various protocols including CalDAV, local ICS files, and Zimbra.

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

## Quick Start

1. Configure your calendars in `~/.syncalpy/config.yaml`
2. Run synchronization: `syncalpy sync`
