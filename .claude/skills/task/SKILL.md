---
name: task
description: Implement ONE task from TASKS.md with objective verification and one commit.
disable-model-invocation: true
argument-hint: "[task ID or text; empty = any ready task]"
---
Do exactly one task and stop.

1. Open `TASKS.md`. Pick the line containing "$ARGUMENTS"; if empty, any ready `- [ ]` task: `DoR: ready`, every dependency `[x]`, no `proposed:` lines. Otherwise record the blocker and stop.
2. Done = its acceptance criteria and DoD additions; each criterion maps to a named test or observable check. Indented `decided:` lines are settled: do not ask about them. `proposed:` lines are unreviewed drafts: stop (unattended: mark `[!]`).
3. On `main`, create `task/<ID>-<slug>` first.
4. Stop and propose a 5-line plan only if the task is ambiguous or touches circuit math, data formats, saves, CD, deletion or a new dependency that is not `decided:`.
5. Read and change files with Read/Grep/Glob/Edit/Write. Unattended: one allowlisted Bash command at a time, no `|`, `&&`, `;` or redirection. Never run `main.py` or the Level Studio directly: they rewrite tracked files; use `scripts/verify.sh`.
6. TDD: failing test first, seen failing for the right reason, then the smallest complete change.
7. Run focused tests with `scripts/verify.sh test test_<name>.py` (worktrees have no interpreter of their own), then `scripts/verify.sh fast`; run `scripts/verify.sh full` once before finishing, unless the prompt says the runner does it.
8. Logic changed in more than 3 files, or a high-risk surface (see `alexandria-loop`): call `alexandria-reviewer` and handle its BLOCKING findings.
9. Mark the task `[x]` and make one commit (`feat(<scope>): …` Conventional Commits, files staged by name). For circuit math, level data, saves or CD, end the body with `Review-attention: <what and where>`. If you cannot finish, mark `[!]` with a `note:` line.
10. Do not start another task. Answer in at most 3 lines: what changed, verify output, commit hash.
