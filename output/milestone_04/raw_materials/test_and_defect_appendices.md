# Appendix D - Test tables and defect register

These are copy-ready appendices for the Milestone 04 report. They summarize the current recorded evidence. Do not describe a headless check as a native desktop check.

## A. Unit and integration test case table

| Test ID | Level | What was checked | Input / action | Expected result | Recorded outcome |
|---|---|---|---|---|---|
| UT-01 | Unit | OBJ polygon edge construction and normalization | A quad described by four vertices and two reversed face records | Four unique boundary edges; normalized coordinates span expected range | Pass (`tests/test_extensions.py`) |
| UT-02 | Unit | OBJ face formats and comments | Face indices in supported `v`, `v/vt`, `v//vn`, and `v/vt/vn` forms | Three edges; comments and ignored records do not break parsing | Pass (`tests/test_extensions.py`) |
| UT-03 | Unit | Invalid OBJ content | Empty/comment-only file, no face, NaN, invalid coordinates, degenerate points | Raise a controlled `ValueError` | Pass (`tests/test_extensions.py`) |
| UT-04 | Unit | Icon bounds and centering | SVG, model, and brand icons at 12, 16, 20, 24, and 32 px | Icon remains inside target bounds and centered within one pixel | Pass (`tests/test_launch_flow.py`) |
| UT-05 | Unit | Projection edge safety | Zero/negative depth, extreme coordinates, infinite focal value | Reject unsafe projected points without producing non-finite screen coordinates | Pass (12 focused engine-edge checks) |
| IT-01 | Integration | Load sample OBJ into scene | Open bundled `house.obj` through `load_obj_file` | Scene selects the new mesh, model library gains it, recent-file setting updates | Pass (`tests/test_file_open.py`) |
| IT-02 | Integration | Failed OBJ open preserves current state | Attempt to load a missing file | Return a readable error and keep model list and selected shape unchanged | Pass (`tests/test_file_open.py`) |
| IT-03 | Integration | Destination navigation | Click Challenges then cycle with Tab | Active destination changes through all four destinations | Pass (`tests/test_dashboard.py`) |
| IT-04 | Integration | Audio controls at compact window width | Change volume and music mute at 1024 px UI width | Slider/toggle/import controls do not overlap; preference is saved | Pass (`tests/test_dashboard.py`) |
| ST-01 | System / headless | Destination rendering | Run landing, Explore, Challenges, Maze, and Shooter capture scenarios | Real app loop completes and captures each destination | Pass for 15 current scenarios; Shooter capture is headless only |
| ST-02 | System / headless | Resize behavior | Eight screen sizes and 50 rapid resize events | No runner errors; application layout remains available | Pass |
| ST-03 | System / headless | Oversized OBJ feedback | Use generated over-limit OBJ fixture | App remains running and shows a controlled rejection state | Pass |

The table lists representative tests rather than every test function. The current complete automated suite recorded 135 passing tests, one warning, and 36 subtests.

## B. Defect register

The severity labels below are practical report labels assigned for presentation. `BUGLOG.md` is the source for the recorded reproduction, cause, fix, and verification. Each fix's detailed guard test is not consistently named in the bug log; where the specific test name was not recorded, this table says so instead of inventing one.

| ID | Severity / area | How found and reproduction | Expected vs actual / root cause | Fix and verification | Guard evidence |
|---|---|---|---|---|---|
| RX-UI-001 | Medium · identity and mesh list | Open Explore and inspect brand and object rows. | Expected distinct RenderX identity and recognizable mesh previews; all rows reused one generic mark due to shared icon selection. | Added RX brand mark and previews projected from mesh edges; inspected current Explore and all destinations. | Headless destination screenshot scenarios; exact unit-test name not separately identified in `BUGLOG.md`. |
| RX-UI-002 | Low · window identity | Start RenderX and inspect window icon; repeat for Breakpoint. | Expected project icon; runtime default was used because display creation did not set a custom icon. | Added shared window-identity helper; headless run recorded 128×128 icon set for RenderX. Breakpoint GL display remains unverified under dummy video. | Headless icon-call evidence; native Breakpoint appearance not verified. |
| RX-CORE-001 | High · projection | Project `(1, 1, 0)` with `near_depth=0`. | Expected reject point before perspective division; depth zero passed a zero near-plane check and raised `ZeroDivisionError`. | Reject zero/negative camera-space depth; 12 engine-edge checks include zero/negative depth and valid positive near-plane crossing. | `tools/qa/engine_edges.py`; engine tests. |
| RX-CORE-002 | High · projection | Project extreme finite coordinates such as `(1e308, 0, 0.1)`. | Expected finite or rejected screen output; multiplication could overflow after input validation. | Added output finiteness checks; tested large perspective/orthographic values and infinite focal length. | `tools/qa/engine_edges.py`; engine tests. |
| RX-UI-003 | Medium · modal input | Open shortcut help, click a destination behind it. | Expected help to capture the click; destination activated because overlay drew over UI without consuming mouse input. | Help captures pointer, wheel, and text input; outside click dismisses and is consumed. Replayed event schedule. | `tools/qa/scenarios/help-dismiss-outside.json` and `help-escape.json`. |
| RX-UI-004 | Low · interaction state | Hover a control and send window-leave; press then lose focus. | Expected clear hover/pressed state; stale visual interaction state remained because leave/focus events did not reset it. | Clears hover/pressed state and resets cursor on leave/focus loss; replayed event schedules. | `tools/qa/scenarios/hover-leave.json`, `press-focus-loss.json`. |
| RX-UI-005 | Low · pointer feedback | Move pointer over buttons, numeric fields, sliders, and splitters. | Expected cursor shape to reflect action; app never requested system cursor changes. | Added cursor mapping; headless runner verified requests, but native cursor appearance could not be observed with SDL dummy driver. | Headless cursor request sequence; manual desktop visual check still needed. |
| RX-UI-006 | Low · typography | Use minimum-size Explore layout and narrow icon-led controls. | Expected label to disappear if it cannot fit; ellipsis could overlap icon because truncation was unconditional. | Omit label when even truncation marker cannot fit; reran typography audit and inspected 1024×640 capture. | Typography audit and minimum-size screenshot; specific automated test name not separately logged. |
| RX-UI-007 | Low · interaction state | Hold a button and move pointer out before release. | Expected pressed state to clear; press remained recorded because leave handler reset hover only. | Clears pressed state on leave while preserving active drag semantics; replayed event schedule. | `tools/qa/scenarios/press-window-leave.json`. |
| RX-UI-008 | Medium · font rendering | Trigger long compact label that needs truncation. | Expected safe clipped label; font lacked Unicode ellipsis and Pygame raised a missing-glyph error. | Changed marker to ASCII three periods; focused font tests and full suite rerun. | `tests/test_ui_fonts.py`. |
| RX-TEST-001 | Low · test reliability | Open OBJ files, then run file-open test in same environment. | Expected isolated recent-file list; test inherited in-memory user history because only settings path was patched. | Reset in-memory recent list within test patch; full suite rerun. | `tests/test_file_open.py`. |

## C. Scope and unmeasured items

| Item | Status |
|---|---|
| Native Windows common workflow (open, navigate, adjust, save preferences, close) | Not confirmed by the headless evidence package; perform once on target computer. |
| Native file picker and drag-and-drop on target Windows configuration | Not measured in the recorded headless run. |
| Live OpenGL Breakpoint gameplay and GPU frame rate | Not measured by SDL dummy-driver screenshot; manually run with OpenGL 3.3 compatible graphics. |
| Physical device audio output and volume behavior | Audio state/control paths are covered by tests; physical playback is not established by headless screenshots. |
| Large external OBJ load time | Not measured. The cited 34.46 MB `model.obj` exceeds the 2 MB cap and is rejected. |
| Lowest FPS / minimum instantaneous frame rate | Not separately reported. Average, p95, and p99 frame time are recorded. |
| 60-second stability run, 10-seed multi-minute fuzz campaign, full text-field audit, every input device | Not claimed as completed. |
| Security penetration test or external audit | Not performed. Basic local file-input checks only. |

## D. What we learned

| Bug group | Examples | Lesson |
|---|---|---|
| Hard-coded sizes and offsets | Compact icons and text truncation | Calculate control layout from the available rectangle and test at small as well as large sizes. |
| State not cleared on exit | Stuck hover or pressed state after leaving/focus loss | Treat pointer exit, focus loss, and cancellation as explicit input events. |
| Overlay input not captured | Clicks passing through shortcut help | Modal layers must consume events before controls underneath receive them. |
| Unsafe numeric edge cases | Zero depth and non-finite projected coordinates | Validate both inputs and calculated outputs at mathematical boundaries. |
| Shared mutable test state | Recent-file test inherited earlier paths | Isolate persistent and in-memory state so results do not depend on test order. |
