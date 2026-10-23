# RenderX interface direction

## Palette

Use a quiet, charcoal technical-tool palette with one mineral-teal accent.
Define colors and component measurements once in `renderx/ui/theme.py`.

| Token | Value | Use |
|---|---|---|
| `CANVAS` | `#101417` | App background |
| `SURFACE_1` | `#171D21` | Main panels |
| `SURFACE_2` | `#20272C` | Fields and nested rows |
| `SURFACE_3` | `#293137` | Hover and raised controls |
| `SURFACE_4` | `#353E44` | Dividers and disabled borders |
| `TEXT` | `#E4E9EB` | Primary text |
| `TEXT_MUTED` | `#A1ADB4` | Secondary text and hints |
| `ACCENT` | `#71C9B3` | Selection and primary actions |
| `SUCCESS` | `#8BBF9B` | Completion feedback |
| `WARNING` | `#D5AD70` | Caution feedback |
| `ERROR` | `#D78178` | Errors and destructive actions |
| `AXIS_X` | `#D27A72` | X axis only |
| `AXIS_Y` | `#87B88A` | Y axis only |
| `AXIS_Z` | `#7C9EC4` | Z axis only |

Body text uses high-contrast neutral foregrounds. Axis hues are confined to the
orientation widget and axis labels. Status colors are reserved for their
meaning, not decoration. Confirm text contrast against every surface when
implementing tokens.

## Type, spacing, and shape

- UI face: bundled **Inter**. Numeric values and coordinates: bundled **IBM Plex
  Mono**. Include their OFL license files and load them by paths relative to the
  package; use Pygame's built-in face only as a missing-file fallback.
- Scale: 11 px micro hint, 12 px secondary label, 13 px control label, 15 px
  body, 18 px section title, 24 px workspace title. Keep roles in one type
  scale and cache the resulting font objects.
- Spacing: 4 px base; use 4/8/12/16/24/32 px steps. Standard border radius is
  4 px, with 2–6 px allowed. Separators use a 1 px hairline.
- Motion: 150 ms ease-out for hover/focus and panel transitions; honor reduced
  animation by allowing transitions to be disabled in the UI state.

## Components

Reusable controls in `renderx/ui/components/`: text button, icon button,
segmented control, toggle, slider, numeric field, dropdown, searchable list,
collapsible section, tooltip, keyboard shortcut hint, split handle, modal,
notification, and status segment. Each interactive control has default, hover,
pressed, focused, disabled, and active states where applicable. Draw icons as
consistent 16/20/24 px line art in `renderx/ui/icons.py`.

`renderx/ui/panels/` contains Scene, Transform, Render, Challenge, Maze, and
Shooter panels. These panels read and dispatch existing app/game state; they do
not own projection, transform, mesh, collision, or game rules. Layout and input
mapping stay in the UI layer.

## Layout wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ RenderX   Explore  Quest  Maze  Shooter  [projection] [render mode] [theme] │
├────────────┬───────────────────────────────────────────────┬─────────────────┤
│ SCENE      │                                               │ TRANSFORM       │
│ Objects    │                                               │ Position X Y Z  │
│            │                                               │ Rotation X Y Z  │
│ View tools │                 3D VIEWPORT                   │ Scale           │
│            │         grid · model · axes · gizmo            ├─────────────────┤
│            │                                               │ DISPLAY         │
│            │                                               │ Projection      │
│            │                                               │ Render mode     │
├────────────┴───────────────────────────────────────────────┴─────────────────┤
│ FPS   vertices   edges   faces   projection · mode   contextual hint         │
└──────────────────────────────────────────────────────────────────────────────┘
```

The central viewport receives remaining space. Left and right split handles
resize their docks; either dock can collapse to a narrow rail. At 1024×640,
keep both docks usable at compact widths and preserve access to their controls;
at larger sizes, let the viewport grow. Challenge, Maze, and Breakpoint retain
their own mode-specific content within the same app shell. The existing engine
continues to draw the 3D content; the UI provides its viewport rectangle,
background grid, axes reference, and status presentation.
