"""Find dead air (silence and/or black frames) in a video and cut it out.

Detection and cut planning are pure Python. Only probing, detection and
rendering shell out to ffmpeg/ffprobe, which must be on PATH.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

Interval = tuple[float, float]

MODES = ("silence", "black", "both")

_SILENCE_START = re.compile(r"silence_start: (-?[\d.]+)")
_SILENCE_END = re.compile(r"silence_end: (-?[\d.]+)")
_BLACK = re.compile(r"black_start:(-?[\d.]+)\s+black_end:(-?[\d.]+)")

MIN_KEEP = 0.1  # seconds; shorter kept slivers are dropped


def require_ffmpeg() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} not found on PATH; install ffmpeg")


def probe(path: Path) -> dict:
    """Return duration (s) and which streams the file has."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    duration = float(data["format"]["duration"])
    kinds = {s.get("codec_type") for s in data.get("streams", [])}
    return {
        "duration": duration,
        "has_audio": "audio" in kinds,
        "has_video": "video" in kinds,
    }


def detect_silence(path: Path, duration: float, noise_db: float,
                   min_len: float) -> list[Interval]:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn",
           "-af", f"silencedetect=noise={noise_db}dB:d={min_len}",
           "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True, check=True).stderr
    intervals: list[Interval] = []
    start: float | None = None
    for line in err.splitlines():
        m = _SILENCE_START.search(line)
        if m:
            start = max(0.0, float(m.group(1)))
            continue
        m = _SILENCE_END.search(line)
        if m and start is not None:
            intervals.append((start, float(m.group(1))))
            start = None
    if start is not None:  # silence runs to the end of the file
        intervals.append((start, duration))
    return intervals


def detect_black(path: Path, min_len: float,
                 picture_threshold: float) -> list[Interval]:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-an",
           "-vf", f"blackdetect=d={min_len}:pic_th={picture_threshold}",
           "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True, check=True).stderr
    return [(float(a), float(b)) for a, b in _BLACK.findall(err)]


# ---- pure interval logic -------------------------------------------------

def merge(intervals: list[Interval]) -> list[Interval]:
    out: list[Interval] = []
    for s, e in sorted(i for i in intervals if i[1] > i[0]):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def intersect(a: list[Interval], b: list[Interval]) -> list[Interval]:
    a, b = merge(a), merge(b)
    out: list[Interval] = []
    i = j = 0
    while i < len(a) and j < len(b):
        s, e = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if e > s:
            out.append((s, e))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def dead_intervals(mode: str, silence: list[Interval],
                   black: list[Interval]) -> list[Interval]:
    """'both' means dead only where the picture is black AND the sound is silent."""
    if mode == "silence":
        return merge(silence)
    if mode == "black":
        return merge(black)
    if mode == "both":
        return intersect(silence, black)
    raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")


def plan_keep(duration: float, dead: list[Interval],
              pad: float) -> list[Interval]:
    """Segments to keep. Each dead interval shrinks by `pad` on both sides so
    some breathing room survives around every cut."""
    shrunk = [(s + pad, e - pad) for s, e in dead]
    shrunk = [(s, e) for s, e in shrunk if e > s]
    keep: list[Interval] = []
    cursor = 0.0
    for s, e in merge(shrunk):
        if s - cursor >= MIN_KEEP:
            keep.append((cursor, s))
        cursor = max(cursor, e)
    if duration - cursor >= MIN_KEEP:
        keep.append((cursor, duration))
    return keep


# ---- rendering -----------------------------------------------------------

def build_filter(keep: list[Interval], has_video: bool, has_audio: bool) -> str:
    parts: list[str] = []
    labels: list[str] = []
    for i, (a, b) in enumerate(keep):
        if has_video:
            parts.append(f"[0:v]trim=start={a:.6f}:end={b:.6f},"
                         f"setpts=PTS-STARTPTS[v{i}]")
            labels.append(f"[v{i}]")
        if has_audio:
            parts.append(f"[0:a]atrim=start={a:.6f}:end={b:.6f},"
                         f"asetpts=PTS-STARTPTS[a{i}]")
            labels.append(f"[a{i}]")
    outs = ""
    if has_video:
        outs += "[outv]"
    if has_audio:
        outs += "[outa]"
    parts.append("".join(labels) +
                 f"concat=n={len(keep)}:v={int(has_video)}:a={int(has_audio)}"
                 f"{outs}")
    return ";".join(parts)


def render(src: Path, dst: Path, keep: list[Interval], info: dict,
           crf: int = 20) -> None:
    filt = build_filter(keep, info["has_video"], info["has_audio"])
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(filt)
        script = f.name
    try:
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-i", str(src), "-filter_complex_script", script]
        if info["has_video"]:
            cmd += ["-map", "[outv]", "-c:v", "libx264", "-preset", "medium",
                    "-crf", str(crf), "-pix_fmt", "yuv420p"]
        if info["has_audio"]:
            cmd += ["-map", "[outa]", "-c:a", "aac", "-b:a", "160k"]
        cmd.append(str(dst))
        subprocess.run(cmd, check=True)
    finally:
        Path(script).unlink(missing_ok=True)


# ---- top level -----------------------------------------------------------

def run(src: Path, dst: Path | None = None, *, mode: str = "silence",
        noise_db: float = -35.0, min_dead: float = 1.0, pad: float = 0.25,
        black_threshold: float = 0.98, crf: int = 20,
        dry_run: bool = False) -> dict:
    """Detect dead space in `src`; render to `dst` unless dry_run.

    Returns a summary dict with the dead and kept intervals and durations.
    """
    require_ffmpeg()
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")
    info = probe(src)
    duration = info["duration"]

    silence: list[Interval] = []
    black: list[Interval] = []
    if mode in ("silence", "both") and info["has_audio"]:
        silence = detect_silence(src, duration, noise_db, min_dead)
    if mode in ("black", "both") and info["has_video"]:
        black = detect_black(src, min_dead, black_threshold)

    dead = dead_intervals(mode, silence, black)
    dead = [(s, e) for s, e in dead if e - s >= min_dead]
    keep = plan_keep(duration, dead, pad)
    kept = sum(e - s for s, e in keep)
    if kept < MIN_KEEP:
        raise RuntimeError("Nothing left after removing dead space; "
                           "try a lower --noise-db or a larger --min-dead.")

    summary = {
        "duration": duration,
        "kept_duration": kept,
        "removed_duration": duration - kept,
        "dead": dead,
        "keep": keep,
        "output": None,
    }
    if not dry_run:
        if dst is None:
            raise ValueError("dst is required unless dry_run is set")
        render(src, dst, keep, info, crf=crf)
        summary["output"] = str(dst)
    return summary
