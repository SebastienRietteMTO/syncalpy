"""CLI entry point."""

import argparse
import sys

from .config import Config
from .sync import run_synchronization


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="syncalpy",
        description="Calendar synchronization tool",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    sync_parser = subparsers.add_parser("sync", help="Run synchronization")
    sync_parser.add_argument(
        "--config",
        "-c",
        help="Path to config file",
        default=None,
    )

    list_parser = subparsers.add_parser("list", help="List synchronizations")
    list_parser.add_argument(
        "--config",
        "-c",
        help="Path to config file",
        default=None,
    )

    status_parser = subparsers.add_parser("status", help="Show status")
    status_parser.add_argument(
        "--config",
        "-c",
        help="Path to config file",
        default=None,
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    config = Config(args.config)

    if args.command == "sync":
        syncs = config.get_synchronizations()
        if not syncs:
            print("No synchronizations configured.")
            print("Add synchronizations to ~/.syncalpy/config.yaml")
            return 1

        for i, sync in enumerate(syncs, 1):
            print(f"\n=== Synchronization {i}/{len(syncs)} ===")
            try:
                run_synchronization(sync, config)
            except (RuntimeError, FileNotFoundError, OSError) as e:
                print(f"Error: {e}")
                return 1

        print("\nAll synchronizations complete.")
        return 0

    if args.command == "list":
        syncs = config.get_synchronizations()
        if not syncs:
            print("No synchronizations configured.")
            return 0

        for i, sync in enumerate(syncs, 1):
            cal1 = sync.get("calendar1", {})
            cal2 = sync.get("calendar2", {})
            print(f"{i}. {cal1.get('name', 'calendar1')} <-> {cal2.get('name', 'calendar2')}")

        return 0

    if args.command == "status":
        state_dir = config.get_state_dir()
        if not state_dir.exists():
            print("No state found. Run sync first.")
            return 0

        state_files = list(state_dir.glob("*.json"))
        if not state_files:
            print("No state found. Run sync first.")
            return 0

        print("Last synchronization state:")
        for state_file in state_files:
            print(f"  - {state_file.stem}")

        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
