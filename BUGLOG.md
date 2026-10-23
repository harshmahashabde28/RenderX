# QA bug log

Findings are recorded before they are considered closed. A fix is only marked
verified after the relevant app path has been run and its output inspected.

## RX-UI-001 — Repeated generic mesh mark in object list

- **Status:** Fixed and verified in a headless app run; Explore screenshot shows
  the RX brand and distinct mesh previews. All four destinations were captured.
- **Reproduce:** Open Explore and inspect the left object catalog. Every mesh
  row displays the same small generic box symbol; the header also uses the same
  generic box as RenderX's brand mark.
- **Expected:** The application has a clear RenderX identity, and existing
  object icons distinguish the selected mesh using its wireframe.
- **Actual:** Header branding and all mesh rows reuse the same generic icon.
- **Root cause:** `ScenePanel.draw` passed the fixed `mesh` icon for every model,
  while `Dashboard._draw_topbar` aliased `cube` to the generic Lucide box.
- **Fix:** Add a distinct RX monogram for the existing brand slots and render
  each existing model-row icon from its actual mesh edges.
- **Verification:** Ran the real app loop headlessly and inspected its Explore,
  Challenges, Maze, and Shooter destination screenshots. Explore rows now show
  distinct projected mesh previews, and the header mark is visibly RX.

## RX-UI-002 — No application window icon

- **Status:** Fixed and verified for the RenderX window; Breakpoint's GL
  display branch is unavailable under SDL's dummy driver.
- **Reproduce:** Start RenderX and inspect the window identity; repeat after
  opening Breakpoint. The title is set, but the app never supplies its own
  window icon.
- **Expected:** Both windows use the clear RenderX RX mark as their icon.
- **Actual:** The runtime's default window icon remains in use.
- **Root cause:** The app sets its caption but does not call
  `pygame.display.set_icon` after creating either display mode.
- **Fix:** Apply a shared window-identity helper after creating the renderer
  and Breakpoint displays. Both receive the bundled RX mark and their own
  title.
- **Verification:** The real headless app run reports title `RenderX`, one
  48×48 `set_icon` call, and a screenshot of the icon with the RX mark. The
  OpenGL-only Breakpoint display could not be created by SDL's dummy driver.

## RX-CORE-001 — Zero-depth point divides when the near plane is zero

- **Status:** Fixed and verified.
- **Reproduce:** Call `project_point((1.0, 1.0, 0.0), near_depth=0.0)`.
- **Expected:** A point on the camera plane is rejected before perspective
  division.
- **Actual:** The projection function raises `ZeroDivisionError`.
- **Root cause:** The guard compares depth only with the supplied near plane;
  when that plane is zero, depth zero passes the guard.
- **Fix:** Reject zero/negative camera-space depths before division while
  retaining positive near-plane intersections from the clipping stage.
- **Verification:** The engine-edge runner confirms zero and negative depths
  return `None`, while a clipped segment ending at the positive near plane
  still renders.

## RX-CORE-002 — Finite extreme coordinates overflow the projected point

- **Status:** Fixed and verified.
- **Reproduce:** Project `(1e308, 0.0, 0.1)` perspectively or
  `(1e308, 0.0, 1.0)` orthographically.
- **Expected:** Projection rejects a result that cannot be represented as
  finite screen coordinates.
- **Actual:** Both functions return an infinite X coordinate.
- **Root cause:** Input finiteness is checked, but output finiteness is not
  checked after multiplying/scaling screen coordinates.
- **Fix:** Reject non-finite screen coordinates after projection as well as
  non-finite inputs.
- **Verification:** The engine-edge runner confirms huge perspective and
  orthographic points and infinite focal lengths return `None`; huge geometry
  also renders without sending invalid coordinates to Pygame.

## RX-UI-003 — Keyboard-help overlay lets clicks reach controls beneath it

- **Status:** Fixed and verified.
- **Reproduce:** Open the keyboard-help overlay, then click the Maze destination
  button behind it.
- **Expected:** The overlay captures the click and closes on an outside click;
  the underlying destination does not activate until a later click.
- **Actual:** The app switches to Maze while leaving the overlay open.
- **Root cause:** Help is drawn over the dashboard, but `Dashboard.events` only
  consumes keyboard input while the overlay is open and has no modal mouse
  capture or dismissal path.
- **Fix:** Capture mouse, wheel, and text input while help is open. An outside
  click dismisses the overlay and is consumed; Esc/F1 dismiss it and restore
  input focus.
- **Verification:** Replayed the original event schedule: the outside click
  left the app on Shooter and closed help. A second schedule verified Esc
  closes help and allows a later Maze click.

## RX-UI-004 — Hover and pressed styles persist after leaving or losing focus

- **Status:** Fixed and verified.
- **Reproduce:** Move onto a destination button, then inject `WINDOWLEAVE`.
  Also press a UI control and lose window focus before releasing the mouse.
- **Expected:** Hover and pressed visuals clear when the pointer leaves or the
  window loses focus.
- **Actual:** The recorded state remains `hover=(destination, Explore)` after
  `WINDOWLEAVE`; focus loss also leaves the pressed action unchanged.
- **Root cause:** Dashboard input handles mouse motion and focus, but does not
  clear its hover/pressed state on `WINDOWLEAVE` or focus-loss events.
- **Fix:** Clear pointer hover when the window loses focus or receives
  `WINDOWLEAVE`; clear pressed actions on focus loss and reset the cursor.
- **Verification:** Replayed both event schedules. The final hover and pressed
  states are empty, the drag state is clear, and the cursor resets to arrow.

## RX-UI-005 — Pointer cursor never reflects the control under it

- **Status:** Fixed; cursor requests verified. Visual cursor appearance is not
  verifiable under SDL's dummy video driver.
- **Reproduce:** Move over a toolbar button, numeric field, slider, or splitter.
- **Expected:** Use the hand cursor for buttons, text cursor for numeric
  fields, and resize/move cursors for sliders and splitters.
- **Actual:** The application never calls `pygame.mouse.set_cursor`; the system
  arrow remains in every interaction state.
- **Root cause:** Dashboard hit testing tracks hover and drag actions but has no
  cursor mapping.
- **Fix:** Add cursor mapping for buttons, numeric fields, sliders, and panel
  splitters; restore the arrow after leaving the window or losing focus.
- **Verification:** Replayed pointer and focus schedules. The runner records
  hand then arrow cursor requests. SDL's dummy driver rejects system cursor
  changes, so the cursor's appearance on a normal desktop display still needs
  a visual check.

## RX-UI-006 — Ellipsis overlaps icons when a compact button has no label room

- **Status:** Fixed and verified.
- **Reproduce:** Run Explore at the 1024×640 minimum layout. Inspect narrow
  icon-led buttons such as the dock collapse control, where the computed label
  width reaches zero.
- **Expected:** A label is omitted when even its ellipsis cannot fit; the icon
  stays clear and centered.
- **Actual:** The text helper still draws an ellipsis wider than the button's
  available label area, so it can overlap the icon.
- **Root cause:** `draw_text` truncates to an ellipsis unconditionally after
  exhausting the source text, without checking whether the ellipsis itself
  fits `max_width`.
- **Fix:** If even the ellipsis cannot fit in the supplied width, draw no label
  and leave the icon centered and unobstructed.
- **Verification:** Re-ran the typography audit at 1024×640 and all four
  destinations. It reports no bounds violations; inspected the minimum-size
  screenshot and confirmed the collapse icon is unobstructed.

## RX-UI-007 — Pressed button state remains after pointer leaves the window

- **Status:** Fixed and verified.
- **Reproduce:** Press and hold the theme button, then send `WINDOWLEAVE`
  before releasing the mouse.
- **Expected:** Clear the button's pressed visual as the pointer leaves the
  window; an actual drag operation may continue until its release/cancel event.
- **Actual:** The hover state clears but `pressed=(theme)` remains recorded.
- **Root cause:** The window-leave handler only clears hover and resets the
  cursor; it leaves the dashboard's pressed action intact.
- **Fix:** Clear the pressed button state along with hover when the pointer
  leaves the window, while allowing an active drag to finish normally.
- **Verification:** Replayed the hold/leave schedule with hover/pressed
  expectations enabled. Both states and drag are clear at exit.

## RX-UI-008 — Compact text truncation requests an unsupported glyph

- **Status:** Fixed and verified.
- **Reproduce:** Draw a long compact button label with a width that fits only
  the truncation mark, such as the `control` type role.
- **Expected:** The bundled UI font renders a clipped label or omits it safely.
- **Actual:** The width measurement accepts the Unicode ellipsis, but rendering
  it raises `pygame.error: Couldn't find glyph`.
- **Root cause:** Inter Variable does not include the Unicode ellipsis glyph,
  and the text helper does not verify glyph availability before rendering.
- **Fix:** Use an ASCII three-period truncation mark supported by the bundled
  typeface.
- **Verification:** Both focused font tests pass, and the full suite passes
  all 102 tests with deprecation warnings treated as errors.

## RX-TEST-001 — OBJ recent-file test depends on prior user settings

- **Status:** Fixed and verified.
- **Reproduce:** Open one or more OBJ files in RenderX, then run
  `tests/test_file_open.py` in the same process environment.
- **Expected:** The test checks that opening its sample OBJ records the sample
  in an isolated recent-file list.
- **Actual:** The test expected a one-item list but inherited real recent paths
  from earlier app use, so it failed even though OBJ loading worked.
- **Root cause:** The test redirected the settings-file path but did not reset
  the module's in-memory recent-file list.
- **Fix:** Reset that in-memory list inside the test's patch context.
- **Verification:** The full test suite passes after the fix with the user's
  settings isolated from QA output.
