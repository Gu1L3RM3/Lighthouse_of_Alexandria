# TASKS

Queue for `/task` and `scripts/ralph.sh`. `.project-status` stays the project's status tracker;
this file holds work that is specified well enough to implement.

Each task is an observable result that fits one session; split it when it does not (`T-02a`).
States: `[ ]` pending · `[x]` done · `[!]` stuck (add a `note:` line below the task).

## Shared Definition of Done

- Each acceptance criterion is evidenced by a named test or a reproducible check.
- `scripts/verify.sh full` passes; visible changes have opened screenshots.
- Docs are updated where a player, teacher or agent needs them.

## Format

`depends on:` is the only blocking relationship. `level-data: yes` allows an unattended run to
edit `assets/maps/` and `code/circuitos/`. Indented `decided:` lines are human decisions;
`proposed:` lines are unreviewed drafts. Cover in `decided:` what applies: new dependency (name
or none), data format change, circuit math, module locations and the pattern to follow.
Optional: `execution: model=<name>, effort=<low|medium|high>, max-turns=<n>, retries=<n>`.

## Now

- [ ] T-01 A phone player can reach the in-game Help button while the Fullscreen button is shown
  value: in landscape the Fullscreen button of the web page covers Help, so touch players cannot open it.
  depends on: none.
  acceptance criteria:
    - at 844x390 with touch, the Fullscreen button overlaps no in-game button (screenshot from `web_smoke.py`).
    - the Fullscreen button stays at least 44 px tall and keyboard focusable.
    - `scripts/verify.sh full` passes.
  DoR: not ready.
  DoD additions: opened screenshots of a level at 844x390.
  open question: where should the button go (another corner, or shown only before the game starts)?

- [ ] T-02 The circuit editor's whole top bar is visible on a 1024x768 screen
  value: at 1024x768 the right-most tool is cut off.
  depends on: none.
  acceptance criteria:
    - every top bar button lies inside the screen at 1024x768, covered by a test.
    - the layout at 1280x720 and 1920x1080 keeps every button visible.
  DoR: ready.
  DoD additions: opened screenshot from `smoke_scenes.py circuit_editor`.

- [ ] T-03 The game is confirmed playable on a real Android phone and on iOS Safari
  value: touch was only checked with emulation.
  depends on: none.
  acceptance criteria:
    - menu, one level and the circuit editor are played on both devices, with the findings recorded.
  DoR: not ready.
  DoD additions: none.
  open question: needs a person with the devices.

- [ ] T-04 The web build runs the same library versions that desktop players get
  value: the browser currently downloads newer pygame-ce and pathfinding than requirements.txt pins.
  depends on: none.
  acceptance criteria:
    - the versions loaded by the web build are either equal to the pinned ones or documented and tested.
  DoR: not ready.
  DoD additions: none.
  open question: pygbag 0.9.3 rejects pins in the PEP 723 block; upgrade pins, vendor wheels, or accept the drift?
