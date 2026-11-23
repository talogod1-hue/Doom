"""Command line: python3 -m storyvid run | queue"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import pipeline, queue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="storyvid")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Make and upload the next story video")
    run_p.add_argument("--story", type=Path, help="Use this story file instead of the queue")
    run_p.add_argument("--dry-run", action="store_true", help="Build the video only; no upload, no archive")
    run_p.add_argument("--no-upload", action="store_true", help="Build and archive, but don't upload")

    sub.add_parser("queue", help="List stories waiting to be posted")

    args = parser.parse_args(argv)
    if args.command == "queue":
        for path in queue.list_queue(pipeline.STORIES / "queue"):
            print(path.name)
        return 0

    result = pipeline.run(story_path=args.story, upload=not args.no_upload, dry_run=args.dry_run)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
