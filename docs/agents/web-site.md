# Game website

The research website is **not** in this public repository. It lives in a private repository
(Next.js + Supabase + Vercel) because it holds student accounts, the admin area and research data.

## Today

- GitHub Pages no longer serves the game, and the itch.io job in `cd.yml` is disabled (`if: false`)
  while the study runs.
- Every release attaches `alexandria-web.tar.gz` (the complete `build/web` directory). The private
  site downloads a pinned release, serves it under its own origin and injects the telemetry bridge.

## Contract with this repository

- The game never contains URLs, keys or student data. Telemetry is opt-in: it only sends events
  when the page defines `window.alexTelemetry` (see `docs/agents/telemetry.md`).
- `window.ALEX_STORAGE_PREFIX`, when set by the page, namespaces localStorage saves per student.
- Changing an event's name or props is a contract change: update `docs/agents/telemetry.md` and
  tell the site's maintainers in the PR body.

## Identity (shared with the site)

Night sky `#0f142a`, sea `#183151`, stone `#b0a688`, flame `#ebb45c`, cream `#f5e6aa`, the Press
Start 2P font for headings only, pixel art drawn with hard edges. Sources: `web/alexandria.tmpl`,
`main_menu_scene.py`, `docs/media/`, `docs/marketing/`.
