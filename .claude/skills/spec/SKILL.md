---
name: spec
description: For a large or ambiguous feature - short interview, a one-page spec and outcome tasks in TASKS.md.
disable-model-invocation: true
argument-hint: "<feature idea>"
---
Idea: $ARGUMENTS

For a change that fits one sentence, use /task instead.

1. Interview with AskUserQuestion in short rounds: behavior, edge cases, constraints, what is out of scope, how we know it works. Skip what the code already answers.
2. Write `docs/plans/<slug>.md`, one page: goal, files and interfaces, out of scope, end-to-end verification.
3. Add tasks to `TASKS.md` in its format. Each fits one session and names an observable result ("a player can …", not "add a class"), with `depends on:` only for real prerequisites, 2–5 acceptance criteria, `level-data: yes` when it edits maps or circuits, and `DoR: not ready` plus `open question:` when something is missing.
4. Implement nothing. End with: "Open a new session and run /task <ID>".
