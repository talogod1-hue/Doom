---
name: arena
description: Pit two candidate solutions against each other on the same task and pick a winner with evidence. Use when the user runs /arena or asks to compare two approaches, implementations, or outputs side by side.
---

# Arena

Compare two candidate solutions to the same task and report which one wins.

## Input

The task description comes from the user's message or `$ARGUMENTS`. If the task is missing, ask for it in one line and stop.

## Procedure

1. Restate the task in one line and list the acceptance criteria you will judge against.
2. Produce Candidate A and Candidate B independently. Each must be a complete, runnable solution, not a sketch. Keep them isolated: work in separate files or a separate git worktree so neither reads the other's output.
3. Verify each candidate by running it or its tests. Record the exact command and the result.
4. Score both on the same criteria:
   - Correctness: passes the acceptance criteria and tests (pass/fail).
   - Simplicity: fewer lines and moving parts, measured not guessed.
   - Risk: new dependencies, side effects, edge cases left unhandled.
5. Declare a winner. If the scores tie, pick the simpler candidate and say so.

## Output

- Task and criteria, one line each.
- Candidate A and Candidate B: a one-line summary each, then the verification command and its result.
- A scoring table with one row per criterion.
- Winner and the single deciding reason.

Do not modify files outside the arena workspace. Do not commit or push unless the user asks.
