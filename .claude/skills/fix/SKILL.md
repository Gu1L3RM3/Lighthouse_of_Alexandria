---
name: fix
description: Fix a bug by first reproducing it with a failing test.
disable-model-invocation: true
argument-hint: "<symptom, where it happens, what was expected>"
---
Bug: $ARGUMENTS

1. Locate the likely spot with targeted search.
2. Write a test that reproduces the symptom and fails for the right reason; show the failure. Use fakes instead of a window (see `CLAUDE.md`). Only visible in a scene or the browser: reproduce with the `playtest` skill and keep the screenshot.
3. Fix the root cause with the smallest change.
4. Run the new test (`scripts/verify.sh test test_<name>.py`), then `scripts/verify.sh full`.
5. One commit `fix(<scope>): …` with the reason in one line.

After two failed attempts, stop, summarize the findings and suggest a fresh session with a sharper prompt.
