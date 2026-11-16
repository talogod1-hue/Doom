"""Jarvis command-line entry point.

Usage:
    python -m jarvis            # interactive text session
    python -m jarvis --speak    # also speak replies aloud if a system voice exists
    python -m jarvis --once "what time is it"
"""

from __future__ import annotations

import argparse
import sys

from .brain import Brain
from .persona import build_system_prompt
from .tools import route_local
from .voice import Voice

BANNER = "JARVIS online. How may I assist you?"


def respond(message: str, brain: Brain) -> str:
    """Local skills first (fast, offline, no API cost), then the language model."""
    return route_local(message) or brain.ask(message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis", description="Personal Jarvis assistant")
    parser.add_argument("--speak", action="store_true", help="speak replies aloud")
    parser.add_argument("--once", metavar="TEXT", help="answer one request and exit")
    args = parser.parse_args(argv)

    brain = Brain(build_system_prompt())
    voice = Voice(enabled=args.speak)

    def say(text: str) -> None:
        print(f"JARVIS: {text}")
        voice.speak(text)

    if args.once:
        say(respond(args.once, brain))
        return 0

    say(BANNER)
    try:
        while True:
            try:
                message = input("you: ").strip()
            except EOFError:
                break
            if not message:
                continue
            reply = respond(message, brain)
            say(reply)
            if message.lower() in {"exit", "quit", "goodbye", "shut down"}:
                break
    except KeyboardInterrupt:
        print()
        say("Goodbye, sir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
