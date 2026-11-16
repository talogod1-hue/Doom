"""Local skills Jarvis can run without an LLM: time, math, notes, system status."""

from __future__ import annotations

import ast
import operator
import os
import platform
import re
import shutil
import json
from datetime import datetime
from pathlib import Path

NOTES_FILE = Path(os.environ.get("JARVIS_NOTES_FILE", Path.home() / ".jarvis_notes.json"))

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(expression: str) -> float:
    """Evaluate arithmetic only. No names, calls, or attribute access."""

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            left, right = _eval(node.left), _eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("exponent too large")
            return _OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError("unsupported expression")

    tree = ast.parse(expression.strip(), mode="eval")
    return _eval(tree)


def current_time() -> str:
    now = datetime.now()
    return f"It is {now:%H:%M}, {now:%A %d %B %Y}."


def system_status() -> str:
    disk = shutil.disk_usage(Path.home())
    free_gb = disk.free / 1e9
    total_gb = disk.total / 1e9
    return (
        f"Host {platform.node()} running {platform.system()} {platform.release()}. "
        f"Disk: {free_gb:.1f} of {total_gb:.1f} GB free. All systems nominal."
    )


def _load_notes() -> list[str]:
    try:
        return json.loads(NOTES_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_notes(notes: list[str]) -> None:
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


def add_note(text: str) -> str:
    notes = _load_notes()
    notes.append(text)
    _save_notes(notes)
    noun = "note" if len(notes) == 1 else "notes"
    return f"Noted. You now have {len(notes)} {noun}."


def list_notes() -> str:
    notes = _load_notes()
    if not notes:
        return "No notes on file."
    return "\n".join(f"{i}. {n}" for i, n in enumerate(notes, 1))


_CALC_RE = re.compile(r"^(?:what(?:'s| is)?|calc(?:ulate)?|compute)?\s*([\d\s\.\+\-\*/%\(\)\^]+)\??$", re.I)


def route_local(message: str) -> str | None:
    """Return a reply if a local skill handles this message, else None."""
    text = message.strip()
    lower = text.lower()

    if lower in {"exit", "quit", "goodbye", "shut down"}:
        return "Goodbye, sir."
    if re.search(r"\b(what(?:'s| is) the )?(time|date|day)\b", lower) and len(lower) < 40:
        return current_time()
    if re.search(r"\b(system|status|diagnostics)\b", lower) and len(lower) < 40:
        return system_status()
    if lower.startswith(("note ", "remember ")):
        return add_note(text.split(" ", 1)[1])
    if lower in {"notes", "list notes", "show notes"}:
        return list_notes()

    match = _CALC_RE.match(text)
    if match and re.search(r"\d", match.group(1)) and re.search(r"[\+\-\*/%\^]", match.group(1)):
        try:
            result = safe_eval(match.group(1).replace("^", "**"))
            return f"That comes to {result:g}."
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError):
            return "I could not compute that, sir."
    return None
