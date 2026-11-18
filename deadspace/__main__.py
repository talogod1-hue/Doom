"""Command line: python3 -m deadspace INPUT [-o OUTPUT] [options]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import core


def _fmt(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    return f"{int(m):d}:{s:06.3f}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="deadspace",
        description="Remove dead air (silence and/or black frames) from a video.",
    )
    p.add_argument("input", type=Path, help="video file (any format ffmpeg reads)")
    p.add_argument("-o", "--output", type=Path,
                   help="output file (default: INPUT_nodead.mp4)")
    p.add_argument("--mode", choices=core.MODES, default="silence",
                   help="silence: cut quiet audio. black: cut black frames. "
                        "both: cut only where black AND silent (default: silence)")
    p.add_argument("--noise-db", type=float, default=-35.0,
                   help="audio below this level counts as silence (default: -35)")
    p.add_argument("--min-dead", type=float, default=1.0,
                   help="shortest stretch (s) worth cutting (default: 1.0)")
    p.add_argument("--pad", type=float, default=0.25,
                   help="seconds kept at each edge of a cut (default: 0.25)")
    p.add_argument("--black-threshold", type=float, default=0.98,
                   help="fraction of black pixels that counts as a black frame "
                        "(default: 0.98)")
    p.add_argument("--crf", type=int, default=20,
                   help="x264 quality, lower is better (default: 20)")
    p.add_argument("--dry-run", action="store_true",
                   help="report what would be cut without writing a file")
    args = p.parse_args(argv)

    src = args.input
    if not src.is_file():
        print(f"error: no such file: {src}", file=sys.stderr)
        return 2
    dst = None
    if not args.dry_run:
        dst = args.output or src.with_name(f"{src.stem}_nodead.mp4")

    try:
        s = core.run(src, dst, mode=args.mode, noise_db=args.noise_db,
                     min_dead=args.min_dead, pad=args.pad,
                     black_threshold=args.black_threshold, crf=args.crf,
                     dry_run=args.dry_run)
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"duration:  {_fmt(s['duration'])}")
    print(f"removed:   {_fmt(s['removed_duration'])} in {len(s['dead'])} cut(s)")
    print(f"kept:      {_fmt(s['kept_duration'])} in {len(s['keep'])} segment(s)")
    for a, b in s["dead"]:
        print(f"  cut {_fmt(a)} -> {_fmt(b)}  ({b - a:.2f}s)")
    if s["output"]:
        print(f"wrote:     {s['output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
