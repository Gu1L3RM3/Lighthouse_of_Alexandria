# Game website

Read before building or changing the website. Nothing is built yet: this is the starting contract.
Plan the site with `/spec` and design it with the `frontend-design` skill.

## Today

GitHub Pages serves the web game itself at the root
(`https://gu1l3rm3.github.io/Lighthouse_of_Alexandria/`), published by `cd.yml` together with every
game release. itch.io hosts the downloads and a browser copy.

## Decide in the first spec

- Where the game moves (proposal: `/jogar/`, with the site at the root). localStorage saves are per
  origin, so a new path on the same origin keeps them; check pygbag's relative asset paths.
- Deploy: a site workflow with `paths:` filters, so site changes do not release the game. One Pages
  deploy must publish site and game together.
- Stack. Prefer static HTML/CSS/JS in `site/` (already excluded from the web bundle) unless the
  content needs a generator.
- Audience: players, teachers (Level Studio), researchers.

## Identity

Take it from the game, not from a template: night sky `#0f142a`, sea `#183151`, stone `#b0a688`,
flame `#ebb45c`, cream `#f5e6aa`, the Press Start 2P font for headings only, pixel art drawn with
hard edges. Sources: `web/alexandria.tmpl`, `main_menu_scene.py`, `docs/media/`,
`docs/marketing/`. Respect the asset pack licences listed in the in-game credits.

## Done means

- Portuguese and English, with the same content in both.
- Checked at 390 px and 1440 px with the Playwright MCP: no horizontal scroll, no overlap, no
  console errors, screenshots opened.
- Keyboard reaches every control with visible focus; text contrast at least 4.5:1; images have
  `alt`; `prefers-reduced-motion` honoured.
- Light: no video or large GIF on first load; images compressed and sized.
- No secrets, trackers or third-party scripts without a decision.
- The security session (`web-security` skill) ends in `SECURITY: PASS`. It runs only for website
  work; its checklist covers what GitHub Pages leaves to the page itself (CSP, referrer policy).
- A repeatable check is added to `scripts/verify.sh` and CI with the first page.
