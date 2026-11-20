"""Command-line interface for automasoc."""

import argparse
from datetime import datetime

from .scheduler import SUPPORTED_PLATFORMS, Scheduler


def main() -> None:
    parser = argparse.ArgumentParser(prog="automasoc")
    parser.add_argument("--store", default="automasoc.json", help="JSON storage file")
    subcommands = parser.add_subparsers(dest="command", required=True)

    schedule = subcommands.add_parser("schedule", help="schedule a post")
    schedule.add_argument("platform", choices=SUPPORTED_PLATFORMS)
    schedule.add_argument("text")
    schedule.add_argument("at", help="ISO-8601 datetime, for example 2026-11-20T12:00:00Z")

    subcommands.add_parser("list", help="list scheduled posts")

    due = subcommands.add_parser("due", help="list posts that are due")
    due.add_argument("--now", help="ISO-8601 datetime override")

    args = parser.parse_args()
    scheduler = Scheduler(args.store)

    if args.command == "schedule":
        post = scheduler.schedule(args.platform, args.text, datetime.fromisoformat(args.at.replace("Z", "+00:00")))
        print(post.id)
    elif args.command == "list":
        for post in scheduler.list():
            print("{}\t{}\t{}\t{}".format(post.id, post.status, post.scheduled_at.isoformat(), post.text))
    elif args.command == "due":
        now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else None
        for post in scheduler.due(now):
            print("{}\t{}\t{}\t{}".format(post.id, post.platform, post.scheduled_at.isoformat(), post.text))


if __name__ == "__main__":
    main()
