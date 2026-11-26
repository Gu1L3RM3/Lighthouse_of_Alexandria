---
name: playtest
description: Run Lighthouse of Alexandria end to end - boot every scene headless, check the web build in Chromium with touch, or explore it with the Playwright MCP. Use when asked to test, run or screenshot the game, its web build or the Level Studio, or to confirm a change works beyond unit tests.
---

# Playtest

All commands run from the repository root. Use `.venv/bin/python` (in a worktree without `.venv`,
the one of the main checkout). The scripts work in a throwaway copy, so saves and circuits are safe.

## Every scene, headless

```sh
.venv/bin/python scripts/smoke_scenes.py --out <dir>             # all scenes + circuit editor
.venv/bin/python scripts/smoke_scenes.py fase_3 help --out <dir> # a subset
```

Fails on a traceback, a non-zero exit, an unknown scene or a missing screenshot. It proves that a
scene boots and draws, not that it can be completed: open the PNGs. The headless display is
1024x768.

## Web build

```sh
scripts/verify.sh web                                       # build, boot desktop + phone, tap
.venv/bin/python scripts/web_smoke.py --out <dir>           # same, choosing the screenshot folder
```

Needs `requirements-e2e.txt`, `playwright install chromium` and network (pygbag runtime CDN).

## Exploring with the Playwright MCP

1. Start the server in the background: `.venv/bin/python scripts/web_smoke.py --serve`; it prints
   the URL.
2. `browser_resize` to 1280x720 (desktop) or 844x390 (phone), then `browser_navigate`.
3. Wait until `document.body.dataset.boot` is `done` (click once if it says `ready`).
4. A `data-crash` attribute on `body` is a Python crash: the console never shows tracebacks.
5. Screenshot as `.playwright-mcp/<name>.png` (a bare name lands in the project root), read
   console errors. Touch needs CDP `Input.dispatchTouchEvent` (see `_tap` in
   `scripts/web_smoke.py`); an MCP click is a mouse event and does not exercise touch handling.

The circuit editor in the browser: set `ALEX_BOOT_EDITOR_FILE` and `ALEX_BOOT_EDITOR_DEBUG=1` at
the top of a scratch copy's `main.py`.

## Level Studio and website

`python tools/level_studio.py` edits real level files: run it only in a worktree. Check Studio and
site pages at 1440 px and 390 px wide, in Portuguese and English, with console errors read.
