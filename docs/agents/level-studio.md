# Level Studio

Read before changing `tools/`, stage data or per-stage tuning. Teacher guide: `docs/level_studio.md`.

- `tools/` is not shipped (excluded in `pygbag.ini`) and never imported by the game.
- Standard-library HTTP server on 127.0.0.1 editing TMX maps (`studio/tmx_io.py`, byte-identical
  round trip), circuits and `level.json`. Keep it local only and keep its cross-site checks.
- The level sequence is the doors' `next_scene`; extra levels live in a stage folder and reuse its
  scene class and validator (`studio/campaign.py`).
- Per-stage tuning: `code/core/level_config.py`.
- It writes straight into `assets/maps/fases` and `code/circuitos`, and several tests read those
  tracked files: try it only in a worktree, or the suite turns red on experimental levels.
