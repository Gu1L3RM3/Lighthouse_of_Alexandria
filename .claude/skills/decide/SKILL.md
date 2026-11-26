---
name: decide
description: Draft the indented `decided:` lines for ONE pending task in TASKS.md (no implementation), so /task and ralph don't stop for decisions.
disable-model-invocation: true
argument-hint: "<task ID>"
---
Prepare exactly one task. Write only `TASKS.md`; implement nothing.

1. Find the `- [ ]` line containing "$ARGUMENTS" (empty: the first pending task without `decided:`/`proposed:` lines).
2. Check the code instead of assuming which modules, data and helpers exist.
3. Draft one indented line per point of the `decided:` checklist in the `TASKS.md` header that applies, plus behavior the criteria leave open. Never decide against `CLAUDE.md`.
4. Too big for one session: split it (`T-12a`, `T-12b`). Never change a done criterion or another task.
5. Open questions: give each a recommended option.
   - Interactive: ask with AskUserQuestion, then write `  decided: …` lines.
   - Unattended (`ralph.sh --plan`): ask nothing; write `  proposed: …` with `(alternative: …)`.
6. Unattended: do not commit (the runner does). Interactive: commit only `TASKS.md` as `docs(tasks): decided lines for <ID>`.
7. Answer in at most 5 lines: task, open questions, chosen answers.
