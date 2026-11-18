---
name: deadspace
description: Remove dead space (silent stretches, and optionally black frames) from any video using the repo's deadspace tool. Use when the user runs /deadspace or asks to cut silence, dead air, or black frames out of a video. Usage - /deadspace <video> [--mode silence|black|both] [--dry-run] [-o OUTPUT] [--noise-db DB] [--min-dead S] [--pad S]
---

# Deadspace

Wraps the `deadspace` command in this repository (`python3 -m deadspace`). It needs `ffmpeg` and `ffprobe` on PATH.

## Input

- Arguments: `$ARGUMENTS`
- If no video path is given, ask for one in one line and stop.
- Pass the arguments through unchanged. Do not invent options the user did not ask for.

## Procedure

1. Check the input file exists. If not, say so and stop.
2. If the user asked only what would be cut, or gave no output path, run the tool with `--dry-run` first and show the result.
3. Otherwise run from the repository root:

   ```bash
   python3 -m deadspace $ARGUMENTS
   ```

4. Report the duration, the total removed, the number of cuts, and the output path, exactly as the tool prints them. If the tool exits non-zero, show its error and stop.
5. Do not commit or push unless the user asks.

## Options

- `--mode silence` (default): cut quiet audio.
- `--mode black`: cut black frames.
- `--mode both`: cut only where the picture is black AND the sound is silent.
- `--noise-db` (default -35), `--min-dead` (default 1.0 s), `--pad` (default 0.25 s), `--black-threshold` (default 0.98), `--crf` (default 20).
