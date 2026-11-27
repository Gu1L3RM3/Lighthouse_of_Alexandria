# Harness

How work gets done and checked in this repository.

## The judge

| Command | Runs | When |
|---|---|---|
| `scripts/verify.sh fast` | ruff (real errors) + unit tests, seconds | Stop hook, while developing |
| `scripts/verify.sh full` | fast + every scene headless + harness tests and web check when those areas changed | done criterion |
| `scripts/verify.sh web` | web build in Chromium, desktop and phone | web and touch work |
| `scripts/verify.sh test test_x.py` | one test file, with the right interpreter | red/green steps |
| `scripts/verify.sh security-needed` | answers whether the website changed | gate of the security session |

`SKIPPED` means a check did not run (missing tool). `HARNESS_STRICT=1` (CI, unattended runs)
turns that into a failure.

Setup, once, in the main checkout (worktrees use its `.venv`):

```sh
pip install -r requirements-e2e.txt && python -m playwright install chromium
```

## Attended loop

| Situation | Use |
|---|---|
| Any change | `/alexandria-loop <goal>`: classifies risk and picks agents and review gates |
| Bug | `/fix <symptom>` |
| Large or uncertain feature | `/spec <idea>`, then `/task` |
| One queued task | `/task [ID]` (`/decide <ID>` first if decisions are open) |
| End-to-end check | `playtest` skill or the `playtester` agent |
| Website change, before shipping | `/web-security` in a fresh session, or the `web-security-reviewer` agent |
| Close a branch | `/ship-branch` (PR + auto-merge on green CI) |
| Repeated mistake | `/lesson <rule>` |

Agents: `alexandria-scout` (map), `alexandria-implementer` (TDD in a worktree),
`alexandria-reviewer` (diff review), `playtester` (screens and browser). At most 3 at once.

## Security session (website only)

Applies to `site/` and `.github/workflows/site*.yml`. The game, its web build and Level Studio are
not in scope. It is read-only and ends in `SECURITY: PASS` or `SECURITY: BLOCKED`:

- attended: `/alexandria-loop` and `/ship-branch` require it;
- unattended: `ralph.sh` runs it as a separate session after the tasks and opens no PR unless the
  last line is `SECURITY: PASS` (a crash, a missing verdict or an edited file also block).

It is a review by a model, not a proof: it does not replace testing the published site.

## Tools in the project

- Playwright MCP (`.mcp.json`, pinned version); approve it once when Claude Code asks.
- `frontend-design` skill (plugin enabled in `.claude/settings.json`); if it is missing, run
  `claude plugin install frontend-design@claude-plugins-official --scope project`.

## Unattended runs

```sh
scripts/wt.sh new night                 # sibling worktree from origin/main
cd ../Lighthouse_of_Alexandria-wt-night
scripts/ralph.sh --plan 3               # drafts proposed: lines; review them into decided:
scripts/ralph.sh 3                      # one clean session per ready task, then ship-branch
scripts/ralph.sh status                 # progress, cost, stuck tasks, saved attempts
```

- Ceilings default to US$ 2 per attempt and US$ 10 per run (`HARNESS_BUDGET_USD`,
  `HARNESS_RUN_BUDGET_USD`); the estimate can be exceeded.
- A task counts only with `[x]`, a commit, no protected file changed and
  `scripts/verify.sh full` passing outside the agent.
- Website changes also need the security session before the PR.
- Failed attempts are kept in `refs/ralph/<ID>/…` before the worktree is reset.
- Protected: `.claude/`, `scripts/`, `.github/`, `ruff.toml`; `assets/maps/` and
  `code/circuitos/` unless the task says `level-data: yes`.

## Limits

- `guard.sh` is a regex safety net, not a sandbox, and tests the agent writes run as your user.
  For unattended work also enable `/sandbox` or use a container.
- The scene smoke proves a scene boots and draws, not that it can be finished.
- Headless Chromium is not a real phone: devices, iOS Safari, audio and controllers stay manual.
- The web check downloads the pygbag runtime, so it fails without network.
