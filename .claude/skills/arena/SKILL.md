---
name: arena
description: Run N independent Claude candidates on the same task, each taking a different approach, verify every candidate, and name the best one that passes. Use when the user runs /arena or asks to compare several approaches side by side. Usage - /arena [N] <task>, N from 2 to 100, default 2.
---

# Arena

Run N isolated candidates on one task, each through a different approach, and keep the best verified result.

## Input

- `N`: the first token of `$ARGUMENTS` if it is an integer. Clamp to 2..100. Default 2.
- Task: the rest of `$ARGUMENTS`. If the task is missing, ask for it in one line and stop.

If N is above 8, state the cost in one line (N parallel agents) and proceed only if the user's request named that N.

## Procedure

1. Restate the task in one line. Write the acceptance criteria as runnable checks (test command, expected output, or a stated property).
2. Assign each candidate a distinct approach before it starts. Keep the list unique: algorithm, data structure, library, or decomposition. Record the list.
3. Launch N candidates in parallel as subagents. Each candidate gets:
   - the task and acceptance criteria,
   - its assigned approach,
   - an isolated git worktree or separate directory, so no candidate reads another's output.
   Each returns: the diff or files it produced, the exact verification command run, and the result.
4. Verify every candidate yourself by re-running its check command. Do not trust a candidate's self-report.
5. Score only candidates that pass. Rank by: passes criteria, then fewer changed lines, then fewer new dependencies.
6. If no candidate passes, report that and do not declare a winner. Include the closest failure and its output.

## Output

- Task and criteria, one line each.
- Approach list, one line per candidate.
- Table: candidate, approach, pass/fail, lines changed, new dependencies.
- Winner and the deciding reason, or "no candidate passed" with the best failure output.

Do not modify files outside the arena workspace. Do not commit or push unless the user asks.
