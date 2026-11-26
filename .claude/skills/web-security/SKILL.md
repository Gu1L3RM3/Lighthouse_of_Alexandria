---
name: web-security
description: Security session for website development (site/ and its deploy workflow), required before a website change ships. Not for the game, its web build or Level Studio.
argument-hint: "[base ref; default origin/main]"
---

# Web security session

A separate, read-only pass over website changes by someone who did not write them: a fresh
session, or the `web-security-reviewer` agent. Never edit, commit or deploy here; a fix is a new
task, followed by a new security session.

## Scope

`scripts/verify.sh security-needed` exits 0 when the website changed since `origin/main` (or the
`HARNESS_BASE` environment variable). Otherwise report "no website changes" and end with
`SECURITY: PASS`. Game code, `web/alexandria.tmpl` and Level Studio are out
of scope.

Review `git diff origin/main...HEAD -- site .github/workflows` (use `$ARGUMENTS` as the base if
given), plus uncommitted and untracked files under `site/`.

## 1. Review the diff

In your own session, also run the built-in `/security-review` and keep the findings that fall in
scope. Where it cannot run (subagent, unattended), say so and rely on the checklist.

## 2. Checklist: static site on GitHub Pages

- **Shared origin**: site and game are served from the same origin, so any script running on a
  site page can read and change the player's saves in localStorage. Rate script injection and
  third-party scripts accordingly.
- **Secrets**: everything under `site/` is public: no keys, tokens or private data, also not in
  comments or source maps.
- **Third parties**: each external script, style, font or iframe is a recorded decision, version
  pinned, with `integrity` and `crossorigin` where possible. No analytics or trackers without one.
- **Injection**: URL, hash, query, storage and `postMessage` values never reach `innerHTML`,
  `document.write`, `eval`, or an `href`/`src` without validation.
- **Headers**: Pages cannot set response headers, so each page carries a
  `Content-Security-Policy` meta tag (no `unsafe-inline` or `unsafe-eval` without a reason) and
  `<meta name="referrer" content="strict-origin-when-cross-origin">`. `frame-ancestors` does not
  work in a meta tag: list clickjacking as residual risk.
- **Links**: https only; `target="_blank"` has `rel="noopener noreferrer"`.
- **Personal data**: forms, sign-ups, contact collection or third-party form services need a
  decision first (Brazilian LGPD; players may be students and minors).
- **Dependencies**: with a package manifest, the lockfile is committed and the audit command was
  run; new packages are justified.
- **Deploy workflow**: minimal `permissions`; third-party actions pinned to a commit SHA; no
  `pull_request_target`; no secrets reachable from fork pull requests; only the site and the game
  build are published.

## 3. Report

One row per finding: severity (HIGH, MEDIUM, LOW), `file:line`, the attack (who does what and
gets what), the smallest fix. Report only what you can point to, and name what you could not check.

The last line is exactly one of:

- `SECURITY: PASS`: everything in scope was checked and there is no HIGH or MEDIUM finding.
- `SECURITY: BLOCKED`: anything else, including a part you could not check.
