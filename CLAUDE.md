# CLAUDE.md

Guidance for Claude Code (and other agents) working on Lighthouse of Alexandria,
a Python/Pygame educational adventure game about electric circuits.

## Quick reference

```bash
pip install -r requirements-dev.txt        # runtime + dev dependencies
python main.py                             # launch the game
scripts/verify.sh fast                     # lint + unit tests (run before every commit)
scripts/verify.sh full                     # done criterion: + every scene, web and harness checks
python -m unittest discover -s code/tests  # unit tests only
python tools/level_studio.py               # Level Studio, the teacher web tool
pyinstaller --noconfirm Alexandria.spec    # desktop release build
pygbag --template web/alexandria.tmpl --icon assets/images/icon/game_icon_64.png --build .    # own site: upload build/web
pygbag --template web/alexandria.tmpl --icon assets/images/icon/game_icon_64.png --archive .  # itch.io: upload build/web.zip
```

- Entry point: `main.py`; game loop and scene registration: `code/game.py`.
- `code/scenes/` scenes, `code/entities/` game objects, `code/core/` shared ECS,
  UI, localization, maps and circuit services. Circuit JSON lives in `code/circuitos/`.
- Tests: standard-library `unittest` in `code/tests/test_*.py`; reusable data in
  `code/tests/fixtures/`. Each test file adds `code/` to `sys.path` itself.
- Harness tests: `pytest` in `scripts/tests/`.
- Commits: Conventional Commits (`feat(circuits): ...`, `fix: ...`, `refactor: ...`).
  Never commit saves or unrelated circuit JSON edits; stage files by name.

## Read when it applies

- `docs/agents/harness.md`: the loop, skills, agents, playtesting, unattended runs.
- `docs/agents/web.md`: web build, touch input, boot screen, circuit editor layout.
- `docs/agents/level-studio.md`: `tools/`, stage data, `level.json`.
- `docs/agents/web-site.md`: the game website.
- `docs/agents/telemetry.md`: research telemetry contract and event table (data dictionary).

## Research telemetry

- Opt-in: off unless the hosting page defines `window.alexTelemetry`; no URLs or secrets in the repo.
- Record with `TelemetryService.get().record(type, **props)`; props stay small, no player free text.
- A new or changed event updates the table in `docs/agents/telemetry.md` in the same commit.

## Delivery

- Work on a branch; `main` receives code only through a PR with the `tests` check green.
- **A merge into `main` is a public release** (tag and GitHub Release; itch.io is paused and Pages removed during the research study), except when
  only documentation or harness files change (`paths-ignore` in `cd.yml`). The owner
  pre-authorized automatic merges: open the PR and run `gh pr merge --squash --auto`, so it
  lands only with CI green. Never `--admin`, never push to `main`, never force-push.
- Website work (`site/`) also needs the security session (`web-security` skill) before it ships.
  Game changes do not.
- Done = `scripts/verify.sh full` passing, shown. Visible changes also need opened screenshots
  (`playtest` skill).

## Working method: TDD

Every behavior change follows red → green → refactor:

1. **Red**: write the smallest failing test that states the expected behavior.
   Run it and confirm it fails for the right reason (not an import typo).
2. **Green**: write the minimum production code that makes it pass.
3. **Refactor**: clean up names and duplication with the suite green.
4. Run `scripts/verify.sh fast` before committing.

Rules:
- Bug fixes start with a test that reproduces the bug.
- Name tests `test_<expected_behavior>`; one behavior per test.
- Test through public interfaces, not private helpers or internal state.
- Use small fakes (e.g. a fake `TiledMap` with `width`, `height`,
  `get_layer_by_name`) instead of loading real maps or opening a window.
- Refactors that should not change behavior rely on the existing tests
  (e.g. `test_circuit_characterization.py`) as a safety net; add a
  characterization test first if the code is not covered.
- Cover both Portuguese and English when localization is touched.

## SOLID, applied to this codebase

- **Single Responsibility**: a module or class has one reason to change.
  Scenes orchestrate; systems hold per-frame logic; `core/circuit_tools`
  holds circuit math. Example: `linear_system.py` only solves `Ax = b`;
  `numeric_solver.py` only builds the MNA matrix from a circuit graph.
- **Open/Closed**: extend through new components, systems, spawners or
  `ElementKind` handling rather than editing unrelated branches of big
  `if` chains in scenes.
- **Liskov Substitution**: subclasses (scenes, spawners, systems) must honor
  the base contract: same method signatures, no surprise exceptions.
- **Interface Segregation**: depend on the narrow surface you use. A
  function that needs `width`, `height` and a layer should not require a
  full scene or `TileMap`.
- **Dependency Inversion**: pass collaborators in (constructor or argument)
  instead of reaching for globals, so tests can substitute fakes.
  Example: `CircuitAnalysisService(solver=...)`.

## Clean code

- Names reveal intent: `solve_linear_system`, `walkable`, not `do_calc`, `arr`.
- Small functions that do one thing; early returns over deep nesting.
- No magic numbers: name constants in `UPPER_SNAKE_CASE`
  (e.g. `SINGULAR_TOLERANCE`).
- Typed, explicit domain errors for circuit problems (`SingularCircuitError`,
  `MissingGroundError`); translate low-level errors at module boundaries
  with `raise ... from exc`.
- Do not mutate inputs unless that is the function's stated purpose.
- Comments explain *why*, not *what*. Delete dead code instead of commenting it out.
- Match the surrounding style (4-space indent, `snake_case`, `PascalCase`
  classes). There is no formatter; avoid unrelated reformatting in diffs.
- Prefer the standard library and existing helpers before adding a dependency.

## Build size rules

The release is a PyInstaller bundle, so every dependency ships to players.

- **No numpy.** It added ~40 MB to the build for one small linear solve.
  Use `core.circuit_tools.linear_system.solve_linear_system` and plain lists.
  `test_no_numpy_runtime.py` guards this: it imports the game and its scenes,
  runs pathfinding and the circuit solver with `import numpy` blocked.
  (`pathfinding` only uses numpy when installed; lists work fine.)
- New runtime dependencies need a size check: build and compare
  `du -sh "dist/Farol de Alexandria"`.
- Prefer compressed audio (`.ogg`) over `.wav`/`.flac` for music.
- Keep `Alexandria.spec` `excludes` in sync with modules the game does not use.
- New local-only folders go in `pygbag.ini` `ignoreDirs`, or players download them.

## Pitfalls

- Running the game or the Level Studio rewrites files in `code/circuitos/` and `code/save/`;
  use `scripts/smoke_scenes.py`, which runs in a throwaway copy.
- Several tests read tracked maps and circuits: an experimental level in the tree fails the suite.
  Do harness and feature work in a worktree (`scripts/wt.sh new <name>`).
- A green unit suite says nothing about the browser: touch, boot and crashes need
  `scripts/verify.sh web`.
