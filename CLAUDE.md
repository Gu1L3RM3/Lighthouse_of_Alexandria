# CLAUDE.md

Guidance for Claude Code (and other agents) working on Lighthouse of Alexandria,
a Python/Pygame educational adventure game about electric circuits.

## Quick reference

```bash
pip install -r requirements-dev.txt        # runtime + dev dependencies
python main.py                             # launch the game
python -m unittest discover -s code/tests  # full test suite (run before every commit)
pyinstaller --noconfirm Alexandria.spec    # release build
pygbag --template web/alexandria.tmpl --icon assets/images/icon/game_icon_64.png --build .    # own site: upload build/web
pygbag --template web/alexandria.tmpl --icon assets/images/icon/game_icon_64.png --archive .  # itch.io: upload build/web.zip
```

- Web build (pygbag): `sys.platform == "emscripten"` → fixed 1280×720 `SCALED`
  window; desktop stays native fullscreen. Saves are mirrored to localStorage
  by `core/web_storage_sync.py`. Runtime deps for the web go in the PEP 723
  block at the top of `main.py`. The boot screen (lighthouse that lights up
  while loading, "click to start" audio gate) lives in `web/alexandria.tmpl`,
  a copy of pygbag 0.9.3's `default.tmpl`; keep its element ids, pygbag's
  loader looks them up. It also shows a "turn your phone" notice in portrait.
- Touch: `core/touch_gamepad.py` draws an on-screen gamepad after the first
  touch and feeds `InputManager` like a physical controller, so new actions
  only need a controller mapping to work on phones too. UI buttons read
  fingers themselves through `core/touch_points.py` (polled by
  `GestureDetector`, so quick taps and buttons nested in composite widgets work).
  The circuit editor sets `shows_touch_gamepad = False`: on touch the held part
  follows the finger and is placed on lift (`core/ui/touch_grid.py`), with
  Rotate/Cancel buttons (`brush_touch_actions.py`). SDL under pygbag sends no
  mouse events for taps, so touch handling must read `TouchPoints`, not
  `MOUSEBUTTONDOWN`. Test web touch with Playwright + CDP `Input.dispatchTouchEvent`;
  to open the editor directly, set `ALEX_BOOT_EDITOR_FILE` (and
  `ALEX_BOOT_EDITOR_DEBUG=1` to keep the inventory) at the top of a scratch copy's `main.py`.
- Circuit editor board: circuits are authored on a 20 x 10 board of 64 px cells
  (x up to 1216, y up to 768). `core/ui/board_view.py` fits it between the top
  bar and the sidebar (whole-pixel cells, never enlarged), so on 1280x720 it is
  drawn at 57 px. Pointer positions go through `board.to_world`, drawing
  through `board.to_screen_rect`; keep world and screen coordinates apart.
- Prompt bars: with the on-screen pad visible, `draw_prompt_hint_row` names the
  pad's buttons and draws the row doubled in the strip between its controls
  (`InputManager.touch_prompt_area`), wrapping to two rows when needed.

- Entry point: `main.py`; game loop and scene registration: `code/game.py`.
- `code/scenes/` scenes, `code/entities/` game objects, `code/core/` shared ECS,
  UI, localization, maps and circuit services. Circuit JSON lives in `code/circuitos/`.
- Tests: standard-library `unittest` in `code/tests/test_*.py`; reusable data in
  `code/tests/fixtures/`. Each test file adds `code/` to `sys.path` itself.
- Commits: Conventional Commits (`feat(circuits): ...`, `fix: ...`, `refactor: ...`).
  Never commit saves or unrelated circuit JSON edits.

## Working method: TDD

Every behavior change follows red → green → refactor:

1. **Red** — write the smallest failing test that states the expected behavior.
   Run it and confirm it fails for the right reason (not an import typo).
2. **Green** — write the minimum production code that makes it pass.
3. **Refactor** — clean up names and duplication with the suite green.
4. Run the full discovery command before committing.

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

- **Single Responsibility** — a module or class has one reason to change.
  Scenes orchestrate; systems hold per-frame logic; `core/circuit_tools`
  holds circuit math. Example: `linear_system.py` only solves `Ax = b`;
  `numeric_solver.py` only builds the MNA matrix from a circuit graph.
- **Open/Closed** — extend through new components, systems, spawners or
  `ElementKind` handling rather than editing unrelated branches of big
  `if` chains in scenes.
- **Liskov Substitution** — subclasses (scenes, spawners, systems) must honor
  the base contract: same method signatures, no surprise exceptions.
- **Interface Segregation** — depend on the narrow surface you use. A
  function that needs `width`, `height` and a layer should not require a
  full scene or `TileMap`.
- **Dependency Inversion** — pass collaborators in (constructor or argument)
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
