---
name: ship-branch
description: Close a work branch - full verification, independent review, push, pull request and auto-merge once CI is green.
disable-model-invocation: true
---
Never push to `main`, never `--admin`, never force-push. The owner pre-authorized automatic merges: interactive sessions enable auto-merge, so the PR lands only when the `tests` check is green (a merge publishes a release). Unattended runs (`ralph.sh`) still stop at the PR.

Unattended runs allow only one command per Bash call, without `&&`, `;`, pipes or redirections.

1. `git status --short`: commit pending work of this branch in coherent pieces, staging by name. Leave unrelated changes (level experiments, figures) alone and mention them.
2. Run `scripts/verify.sh full`, unless the file named by `git rev-parse --git-path harness-full-verified` contains `git rev-parse HEAD`. A `SKIPPED` line means that check did not run: report it.
3. Call `alexandria-reviewer` on `git diff origin/main...HEAD`. Fix BLOCKING findings (one `fix:` commit each), verify and re-review them.
4. Website changes only (`scripts/verify.sh security-needed` exits 0): ship only with a passed security session for this HEAD. The file named by `git rev-parse --git-path harness-security-passed` containing `git rev-parse HEAD` proves it. Otherwise, interactive: run `web-security-reviewer` and continue only on `SECURITY: PASS`; unattended: stop and report. Commits made after the session need a new one.
5. A new command or convention goes into `CLAUDE.md` or `docs/agents/`.
6. `git push -u origin <branch>` and `gh pr create --base main`. Body: "What changes", "Verification" (criterion → test, screenshots for visible changes), "Security" (website changes: the verdict and open LOW findings), "Review attention" (the `Review-attention:` lines).
7. Interactive sessions: `gh pr merge --squash --auto --delete-branch`, then `gh pr checks --watch`; a red check is new work on the branch. If `.project-status` tracks this work, update the task and sync it with pgui.
8. Answer in at most 6 lines: what the branch delivers, verify result, open findings, PR link.
