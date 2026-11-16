# Jarvis

A personal AI assistant in the spirit of Jarvis. Dependency-free Python 3.10+.

## What it does

- **Local skills (offline, no API cost):** time and date, arithmetic, system status, quick notes.
- **Conversation:** anything else goes to Claude when `ANTHROPIC_API_KEY` is set, under a Jarvis persona.
- **Voice output (optional):** speaks replies via `say` (macOS) or `espeak` / `espeak-ng` (Linux).

## Run it

```bash
export ANTHROPIC_API_KEY=your-key          # optional, enables open conversation
export JARVIS_USER_NAME="Alex"             # optional
export JARVIS_HONORIFIC="sir"              # optional
export JARVIS_MODEL="claude-sonnet-5-5"    # optional

python3 -m jarvis                          # interactive session
python3 -m jarvis --speak                  # with spoken replies
python3 -m jarvis --once "what is 12 * 7"  # single request
```

Notes are stored in `~/.jarvis_notes.json` (override with `JARVIS_NOTES_FILE`).

## Test

```bash
python3 -m unittest tests.test_jarvis -v
```

## Layout

| File | Role |
|------|------|
| `jarvis/main.py` | CLI loop; local skills first, then the LLM |
| `jarvis/tools.py` | Local skills and a safe arithmetic evaluator |
| `jarvis/brain.py` | Anthropic Messages API client (stdlib HTTP) |
| `jarvis/persona.py` | Jarvis system prompt |
| `jarvis/voice.py` | Optional OS speech output |

## Not yet included

Speech input (microphone), wake word, and device control (smart home, app launching). These need extra dependencies and platform-specific setup; they can be added as separate modules without changing the core.
