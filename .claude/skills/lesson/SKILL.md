---
name: lesson
description: Record a repeated mistake or non-obvious pitfall as one line in CLAUDE.md, or turn it into an automatic check.
disable-model-invocation: true
argument-hint: "<what went wrong and the rule that avoids it>"
---
Lesson: $ARGUMENTS

1. If a test, lint rule or hook can catch it, propose that check instead of prose: a check never gets ignored.
2. Otherwise add ONE imperative, verifiable line to "Pitfalls" in `CLAUDE.md`; improve a similar line instead of duplicating.
3. Skip it if the model already gets it right without the rule. Prune obsolete lines; keep the section under 15 lines.
4. Show the diff; do not commit.
