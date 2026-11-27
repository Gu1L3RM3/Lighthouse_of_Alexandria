# Research telemetry

Opt-in event log for studies run on a hosting website. Code: `code/core/telemetry/`. The game holds no
URL, endpoint or secret; it records nothing unless the page defines `window.alexTelemetry`
(desktop, itch.io and tests get `NullTransport`, which drops events before queuing them).

## Contract with the hosting page

- `window.alexTelemetry.push(json)`: `json` is a JSON array of events. A JS exception is swallowed and the
  same batch is retried on the next flush. At most one batch (≤ 200 events) per second, plus a full
  drain on a clean shutdown. A closed tab sends no `session_end` and can lose the last second.
- Event: `{"v":1, "seq":n, "session_id":hex, "t_ms":n, "ts":iso, "scene":name|null, "type":str, "props":{}}`.
  `seq` starts at 1 and grows by one per session; `session_id` is a new uuid4 hex per launch; `t_ms` is
  monotonic ms since launch; `ts` is UTC (`...Z`); `scene` is the active scene name.
- The queue keeps 2000 events; overflow drops the oldest and the next flush sends `telemetry_dropped {count}`.
- `window.ALEX_STORAGE_PREFIX` (optional string) replaces the `alexandria:` localStorage key prefix, so
  students sharing a browser keep separate saves.
- Props never hold player free text or personal data. Non-finite numbers become `null`.

## Events

| type | when | props |
|---|---|---|
| session_start | game launched | game_version (`VERSION` file or `dev`), language, platform web/desktop, viewport_w, viewport_h, input_source |
| session_end | clean shutdown | duration_ms, active_ms |
| scene_enter | active scene name changes | scene, category menu/intro/story/explanation/puzzle/cutscene/editor |
| scene_exit | before the next scene_enter | scene, category, duration_ms, active_ms |
| editor_open / editor_close | circuit editor shown / left (it keeps the level's scene name) | panel_file (`bombs/bomb_editor` for kind bomb), kind panel/bomb; close adds duration_ms, active_ms, saved |
| circuit_submit | editor Save (also Save & exit) | panel_file, solvable, error_kind, component_counts {kind: n}, resistor_values, source_values {kind: [values]}, edits {placed, deleted, rotated, cleared} since editor_open |
| panel_status | only on a status transition per panel, never per validator poll (a transition to wrong_answer is one attempt) | panel_id, panel_file, status, measured, expected, tolerance_percent, solution_type |
| panel_solved | a panel accepts the circuit | panel_id, panel_file |
| panel_reverted | final level: a solved panel's timer runs out | panel_id, panel_file |
| level_complete | door entered; final level all panels solved | scene, next_scene |
| player_death | a life is lost | cause enemy/fall/own_bomb, lives_before, lives_after, game_over, tile_x, tile_y |
| game_over / level_retry | death screen resolves | game_over: scene, return_scene; level_retry: scene, lives |
| bomb_calibrated | bomb circuit gives new parameters | voltage_r1, current_r1, explosion_delay, explosion_radius, damage, used_fallback |
| bomb_placed / bomb_unavailable | bomb key with / without bombs left | placed: remaining, delay, radius, damage, tile_x, tile_y |
| bomb_exploded | a bomb goes off | enemies_hit, enemies_killed, webs_destroyed, self_hit |
| dialogue_start / dialogue_end | dialogue box opens / closes | dialogue_id, lines; end adds duration_ms |
| explanation_slide | explanation scene leaves a slide | dialogue_id, index, duration_ms |
| old_paper_open / old_paper_close | hint paper shown / closed | close: duration_ms |
| item_collected | pickup | item key/resistor/voltage_source/current_source/crystal_invisibility/anti_reaggro_flask; value, area_id for parts |
| pause_open / pause_close | menu opened in game / resumed | close: duration_ms |
| help_open / help_close | help opened / left | close: duration_ms |
| new_game / continue_game | main menu choice | continue: scene, from_save |
| language_change | language toggled | from, to |
| input_source_change | keyboard/mouse/controller/touch switch | source |
| idle_start / idle_end | 60 s without input / next input | end: idle_ms (from idle_start) |
| visibility | `document.visibilityState` changes (polled each second, web) | state |
| telemetry_dropped | queue overflowed | count |

On shutdown the order is idle_end, editor_close, scene_exit (open ones only), then session_end and a full flush.
`panel_file` is always the full relative path (`generic_levels_3/fase_3/pannel1`), unique across levels.
`active_ms` (scene_exit, editor_close, session_end) already excludes idle time (after idle_start) and hidden-page time; a frame gap over 5 s counts as 5 s.
Stick axes are not input for idle detection (analog drift). `scene_exit.duration_ms` of a level includes
its editor sessions.

## Adding an event

Record with `TelemetryService.get().record("type", **props)` (it never raises), or subscribe a listener in
`core/telemetry/event_listeners.py` with `EventManager.subscribe_persistent` (survives `clear()` on scene
changes). Install a recording service in tests with `tests/telemetry_fakes.install_memory_telemetry`, add a
row above, and tell the website owners: this table is the study's data dictionary.
