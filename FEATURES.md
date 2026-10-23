# RenderX feature inventory

This inventory records active behavior, controls, and visible UI retained by
the redesigned interface. The renderer and game systems remain the source of
truth. Items below were checked against the implementation, automated suite,
and destination screenshots at the listed window sizes.

## Application shell and window

- [x] Open RenderX on the landing page by default, then enter Explore without
  remembering the last page.
- [x] Keep the landing reachable from the RenderX brand button, File menu, and
  `Ctrl/Cmd+Shift+H`; confirm before leaving an active Maze or Shooter run.
- [x] Retain Explore, Challenges, Maze, and Shooter destinations in that order.
- [x] Navigate by the measured-width destination tabs, `Tab`, and
  `Ctrl/Cmd+Alt+1…4` shortcuts.
- [x] Support `--skip-landing` and `--mode {explore,challenge,maze,shooter}`
  for development and testing.
- [x] Retain window close, `Esc` app exit behavior outside Maze, focus handling,
  resize, high-DPI sizing, and the shooter window handoff/return.
- [x] Retain saved light/dark theme choice and apply it across the app shell.
- [x] Retain transient feedback for OBJ success/failure and screenshot
  success/failure.
- [x] Retain canvas-to-window pointer mapping and correct hit testing when the
  window is resized.

## Explore: mesh and renderer

- [x] Keep the 17 procedural meshes: Cube, Pyramid, Rectangular prism,
  Tetrahedron, Octahedron, Triangular prism, Hexagonal prism, Cylinder, Cone,
  Sphere, Torus, Plane, Saddle, Ripple, Helix, Möbius ribbon, and Signal wave.
- [x] Keep sample Wavefront OBJ import from the built-in house via the shape
  picker or `O`, including parser warnings and readable errors.
- [x] Keep Wireframe, Hidden line, Solid, and Depth render modes, including the
  existing `M` cycle shortcut.
- [x] Keep Perspective and Orthographic projection, including `P`.
- [x] Keep axes visibility, including `X`.
- [x] Keep per-object rotation, translation, scaling, and reset.
- [x] Keep the animated Signal wave and its play/pause control and `Space`
  shortcut.
- [x] Keep the existing canvas gestures in RenderX Classic: left drag orbits;
  Shift+left drag and middle drag pan; right drag rotates about Z; wheel scales
  while over the viewport.
- [x] Default to Orbit Viewer gestures: left drag orbits; right and middle drag
  pan; Shift+left drag remains a pan alias; wheel zooms. A short right-click
  opens a context menu without breaking right-drag navigation.
- [x] Keep held-key transforms: arrows rotate X/Y; `Q`/`E` rotate Z; `W`/`A`/
  `S`/`D` move X/Y; Page Up/Page Down move depth; `+`/`-` scale.
- [x] Keep shape shortcuts `1` Cube, `2` Pyramid, `3` Rectangular prism; `R`
  reset; `F12` save a screenshot to `screenshots/`.
- [x] Add Ctrl/Cmd+O OBJ open, Ctrl/Cmd+S screenshot export, Ctrl/Cmd+Q and
  Alt+F4 quit, F11 fullscreen, Ctrl/Cmd+, preferences, and F1/? help while
  preserving the original sample, transform, maze, challenge, and game keys.
- [x] Add standard front/right/top views, opposite views, projection aliases,
  the clickable axis gizmo, viewport/object context menus, and a live shortcut
  list generated from the shared input map.
- [x] Add Open Recent and drag-and-drop OBJ loading. Keep the source files
  untouched and remember recent paths in platform settings.
- [x] Keep the active page's real model counts, camera projection, render mode,
  and FPS available as status information; pages without a model show relevant
  campaign or challenge status.

## Challenges

- [x] Keep all three projection challenges and their existing progression:
  Shape Match, Depth and Projection, and Clipping Rescue.
- [x] Shape Match retains target comparison, alignment feedback, X/Y/Z rotate
  buttons, and keyboard/mouse rotation.
- [x] Depth and Projection retains the simultaneous Perspective and
  Orthographic views, depth controls, gated answer choices, feedback, and
  explanation.
- [x] Clipping Rescue retains the near-plane guide, object depth, clipped-edge
  count, depth controls, gated answers, feedback, and explanation.
- [x] Keep answer validation, attempts, confirmation, Next, completion, and
  return to Explore.
- [x] Keep challenge-specific input filtering so unrelated transforms cannot
  alter the exercise.

## Maze campaign

- [x] Keep the three-stage first-person wireframe maze campaign, seeded maze
  layout, two collectible signal keys, locked/unlocked exit, and campaign
  completion.
- [x] Keep the explored minimap, scan pulse with three charges, key/exit/player
  markers, elapsed time, score, best score, and status messages.
- [x] Keep Perspective/Orthographic switching with `P`, scan with `Space`, new
  run with `R`, and continue with `Enter` or `C` after a cleared level.
- [x] Keep movement with arrows or `W`/`A`/`S`/`D`, `Q`/`E` strafing, left-drag
  mouse look, and the on-screen turn/move/pause/scan/projection/run controls.
- [x] Keep pause/resume with `Esc`, focus-loss pausing, level-clear and campaign
  completion states, and score persistence.

## Breakpoint shooter

- [x] Keep the separate resizable OpenGL 3.3 shooter window and return-to-RenderX
  behavior.
- [x] Keep menu, best-run display, Start, Easy/Normal/Hard choice, Deploy, Back,
  pause/resume, restart, return-to-menu, game-over, and return-to-RenderX
  actions.
- [x] Keep movement with `W`/`A`/`S`/`D` or arrows; mouse aim; left mouse or
  `Space` fire; `Shift` dash; `Esc` pause/resume; `F11` fullscreen.
- [x] Keep enemy AI and projectiles, escalating endless waves, elite contacts,
  destructible cover, field supplies, damage/invulnerability, kill streaks,
  score, saved best run, and focus-loss pause.
- [x] Keep health, score, wave, hostiles, elapsed time, minimap, crosshair, and
  contextual wave/combat messages in the HUD.
- [x] Keep all bundled models, textures, shaders, and upstream attribution and
  license.

## New interface requirements

- [x] Add the docked editor layout, restrained dark palette, viewport-first
  hierarchy, and responsive behavior from `DESIGN.md`.
- [x] Add collapsible and resizable left/right docks without hiding the only
  access to any inventoried feature.
- [x] Add a bottom status strip with live FPS, mesh counts, projection/render
  mode, camera/scene status, and a contextual hint.
- [x] Add the orientation widget, axis reference, and subtle viewport grid
  without changing renderer or projection math.
- [x] Add locally bundled UI and monospace fonts with licenses and a local
  fallback; keep all font creation cached.
- [x] Keep native render-mode selection keyboard navigable, make sliders
  support fine/snap adjustments, and double-click a slider to restore its
  default value.
- [x] Add reusable, keyboard-focusable UI components with visible default,
  hover, pressed, focused, disabled, and active states.
- [x] Add keyboard shortcut help on `?` and `F1`; do not remap existing keys.
- [x] Scope shortcut help to the active destination; include Getting started,
  About, and Escape dismissal for the active overlay.
- [x] Add Open Recent, Preferences, and Quit to the File popover while keeping
  view actions in the viewport toolbar/context menu.
- [x] Add clear loading, empty, error, and confirmation feedback where the
  existing app has an applicable state.
- [x] Keep interaction and drawing smooth at 1024×640, 1280×720, 1360×900,
  1920×1080, fullscreen, and HiDPI scales.

## Final verification

- [x] Run the existing automated suite and compare behavior against the
  inventory.
- [x] Exercise each destination, existing mouse gesture, key binding, import,
  screenshot, game state, and resize path.
- [x] Capture and inspect 1280×720 and 1920×1080 screenshots; also check the
  1024×640 layout for clipping and control access.
- [x] Review every checklist item above and leave none unverified.
