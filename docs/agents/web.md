# Web build, touch and the circuit editor

Read before changing the web build, touch input or editor layout.

## Web build (pygbag)

- `sys.platform == "emscripten"` → fixed 1280x720 `SCALED` window; desktop stays native fullscreen.
- Saves are mirrored to localStorage by `core/web_storage_sync.py`.
- Runtime dependencies for the web go in the PEP 723 block at the top of `main.py`; pygbag 0.9.3
  rejects version pins there, so the browser downloads current releases, which can differ from
  `requirements.txt`.
- Everything in the tree is bundled unless `pygbag.ini` excludes it
  (`code/tests/test_web_bundle_excludes.py`).
- The boot screen (lighthouse that lights up while loading, "click to start" audio gate, portrait
  notice, Fullscreen button) lives in `web/alexandria.tmpl`, a copy of pygbag 0.9.3's
  `default.tmpl`. Keep its element ids: pygbag's loader looks them up.
- A Python traceback never reaches the browser console. `main.py` publishes crashes as
  `body[data-crash]` (`core/crash_report.py`); boot progress is `body[data-boot]`
  (`download`, `unpack`, `ready`, `installing`, `done`).
- `ready` appears only when the browser blocks audio until a click.

## Touch

- `core/touch_gamepad.py` draws an on-screen gamepad after the first touch and feeds
  `InputManager` like a physical controller, so a new action only needs a controller mapping.
- UI buttons read fingers through `core/touch_points.py` (polled by `GestureDetector`, so quick
  taps and buttons nested in composite widgets work).
- SDL under pygbag sends no mouse events for taps: touch handling must read `TouchPoints`, not
  `MOUSEBUTTONDOWN`.
- Prompt bars: with the pad visible, `draw_prompt_hint_row` names the pad's buttons and draws the
  row doubled in the strip between its controls (`InputManager.touch_prompt_area`), wrapping to
  two rows when needed.
- Test web touch with Playwright and CDP `Input.dispatchTouchEvent` (`scripts/web_smoke.py`).

## Circuit editor

- It sets `shows_touch_gamepad = False`: on touch the held part follows the finger and is placed
  on lift (`core/ui/touch_grid.py`), with Rotate/Cancel buttons (`brush_touch_actions.py`).
- To open it directly in the browser, set `ALEX_BOOT_EDITOR_FILE` (and `ALEX_BOOT_EDITOR_DEBUG=1`
  to keep the inventory) at the top of a scratch copy's `main.py`.
- Circuits are authored on a 20x10 board of 64 px cells (x up to 1216, y up to 768).
  `core/ui/board_view.py` fits it between the top bar and the sidebar (whole-pixel cells, never
  enlarged), so at 1280x720 it is drawn at 57 px. Pointer positions go through `board.to_world`,
  drawing through `board.to_screen_rect`; keep world and screen coordinates apart.
