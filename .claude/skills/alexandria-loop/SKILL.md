---
name: alexandria-loop
description: Run the lean Lighthouse of Alexandria engineering loop.
disable-model-invocation: true
argument-hint: "<change or goal>"
---

# Alexandria loop

Change requested: $ARGUMENTS

Work in a branch from an up-to-date `main` (`scripts/wt.sh new <name>` when the main checkout has
uncommitted work). Before implementing, state a **loop card**: surface, owner (you or an agent),
smallest command that can turn red, review gate.

## Classify

- **Isolated:** one production surface; no shared data format, circuit math, save, web/touch or
  release behavior.
- **Behavioral:** one behavior changes without crossing a data or platform contract.
- **High risk:** circuit solver or validator, circuit JSON, TMX `next_scene` chain, `level.json`,
  saves, web build or touch, Level Studio file writes, CI/CD, a new dependency.
- **Feature:** more than one independent slice or an open product decision.

Read only the relevant source, callers, tests and `docs/agents/`. Use `alexandria-scout` only when
independent surfaces need mapping.

## Dispatch

- **Isolated:** implement directly, or one `alexandria-implementer`. No review agent.
- **Behavioral:** implement (TDD), then `alexandria-reviewer` once the focused tests pass.
- **High risk:** one owner for the shared contract; tests on both sides of it; `playtester`;
  finish with `/code-review`.
- **Feature:** `/spec`, then one `/task` per task in `TASKS.md`.

Web UI work (website, `web/alexandria.tmpl`, Level Studio screens): load the `frontend-design`
skill before designing, and read `docs/agents/web-site.md` for the site.

Run independent tasks in parallel only in separate worktrees, at most two implementers plus one
scout, reviewer or playtester. Web builds run one at a time.

## Security session (website only)

When `scripts/verify.sh security-needed` exits 0, after `verify.sh full` and before shipping:
dispatch `web-security-reviewer` (clean context) and run `/security-review`. `SECURITY: BLOCKED`
means fix the findings as new work and run the session again. Game changes skip this section.

## Verify and report

Done = `scripts/verify.sh full` passing, with its output shown. Visible changes also need opened
screenshots. Report the loop card, agents used, evidence, findings, and why a review gate was
skipped or escalated. A mistake that happened twice goes to `/lesson`.
