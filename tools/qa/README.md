# RenderX QA harness

`headless_runner.py` runs the real application loop with SDL's dummy video and
audio drivers. It accepts deterministic input schedules, captures the display,
and logs exceptions that escape the app's event, update, or draw boundaries.
The app's local data is redirected into the selected output folder so QA runs do
not overwrite a user's theme, sound, or score settings.

Examples from the repository root:

```powershell
python -W error::DeprecationWarning tools/qa/headless_runner.py --scenario idle --frames 300 --capture 1,150,300
python tools/qa/headless_runner.py --scenario orbit --frames 180 --capture 1,90,180
python tools/qa/headless_runner.py --scenario largest --frames 300 --capture 1,150,300
python tools/qa/headless_runner.py --fuzz-seed 31 --frames 10800 --capture ""
python tools/qa/resize_matrix.py "$env:TEMP\renderx-qa-resize"
python tools/qa/engine_edges.py
python tools/qa/fuzz_batch.py --minutes 3 --seeds 0,1,2,3,4,5,6,7,8,9 --pace --output "$env:TEMP\renderx-qa-fuzz"
python tools/qa/performance_runs.py --seconds 60 --output "$env:TEMP\renderx-qa-performance"
```

The summary includes frame count, injected event count, app-loop frame-time and
dashboard draw-time averages/95th/99th percentiles, destination, and captured
screenshots. Use `--pace` for
wall-clock-duration stability runs. Outputs are written under
`tools/qa/output/latest` by default; set `--output` to keep separate runs.

An event schedule is a JSON array. Each `frame` entry can contain one or more
Pygame event descriptions, for example:

```json
[
  {"frame": 1, "events": [{"type": "mouse_down", "pos": [650, 420], "button": 1}]},
  {"frame": 2, "events": [{"type": "mouse_move", "pos": [700, 460], "rel": [50, 40], "buttons": [1, 0, 0]}]},
  {"frame": 3, "events": [{"type": "mouse_up", "pos": [-10, -10], "button": 1}]},
  {"frame": 4, "events": [{"type": "resize", "size": [1280, 720]}]}
]
```

Schedules can also target live dashboard actions, so the harness follows the
current layout instead of relying on hard-coded coordinates:

```json
[
  {"frame": 1, "events": [{"type": "click_action", "action": ["destination", "Explore"]}]},
  {"frame": 4, "events": [{"type": "move_to_action", "action": ["theme"]}]}
]
```

The included scenarios cover help dismissal, focus loss during drag, numeric
field edge values, and pointer leave/focus cleanup. `engine_edges.py` exercises
projection and OBJ boundary inputs. `resize_matrix.py` checks the eight target
window sizes and fifty rapid resize events. `fuzz_batch.py` uses a fresh
isolated app-data directory per seed and writes a batch summary. Performance
runs report app-loop frame-time average, p95, and p99, plus separate dashboard
draw timings. Compare results on the same machine because headless surface size
and hardware change absolute timings. Add `--audit-text` to check helper-rendered
text bounds, type roles, bundled font files, and font-cache reuse across visible
destinations. The long fuzz and performance scripts also sample working-set
memory every 600 frames where the operating system exposes it.

The dummy SDL driver cannot visually display operating-system cursors or open
the OpenGL-only Breakpoint display. The runner records requested cursor types,
window title/icon, screenshots, and the limitation in its summary/log.

The fuzz mode uses a fixed random seed and the live component rectangles from
the application. It varies destination and toolbar clicks, viewport drags,
wheel input, key pairs, resize, and focus changes. Avoid using a seed on a run
whose input schedule should stay fixed.
