# RenderX — 3D Wireframe Rendering Engine & Learning Laboratory

**Version 3 (Milestone 03: Implementation / Development)**

RenderX is a 3D wireframe renderer built from scratch with **Python and Pygame**. It converts 3D model coordinates into 2D screen coordinates using explicit, readable mathematics (no OpenGL, no NumPy, no 3D engine) and draws the result as a wireframe.

Version 3 turns the original renderer into the **RenderX Learning Laboratory**: the app shows the intermediate values of its own rendering pipeline, so you can point at a number on screen and see which formula produced it.

![RenderX Explore mode](docs/screenshots/explore.png)

---

## Features

**Core renderer**

- Built-in models: cube, pyramid, rectangular prism
- 3D translation, rotation about X / Y / Z, and scaling
- Perspective and orthographic projection (toggle with `P`)
- Coordinate axes (toggle with `X`)
- Near-plane edge clipping in camera space
- Basic OBJ loading (`v` and `f` records) with a sample `house.obj`
- Screenshot export to a unique timestamped PNG (`F12`)
- HUD / information panel, keyboard and mouse controls
- Automated test suite (86 tests)

**Learning Laboratory (Version 3)**

- 15 built-in and procedural models (prisms, cylinder, cone, sphere, torus, plane, saddle, ripple, helix, and more)
- Clickable dashboard with plain-language buttons and hover help
- Seven modes:

| Mode | What it does |
|---|---|
| Explore | Drag, rotate, move, resize and switch models |
| How it works | Traces one selected vertex through eight coordinate stages with formulas |
| Compare views | Perspective and orthographic views side by side, sharing one scene |
| Shape details | Vertex/edge/face counts, bounds, normalisation and topology checks |
| Lessons | 14 short lessons, including clipping and transformation-order experiments |
| Quiz | 10 deterministic multiple-choice questions with hints, score and retry |
| Guided demo | 8 presenter-advanced steps that reuse the real screens |

- Automatic window fit for different screen sizes (proportional scaling, correct mouse mapping)

| Pipeline inspector | Compare views |
|---|---|
| ![Pipeline mode](docs/screenshots/pipeline.png) | ![Compare mode](docs/screenshots/compare.png) |

| Near-plane clipping lesson | Shape details |
|---|---|
| ![Clipping lesson](docs/screenshots/clipping.png) | ![Mesh inspector](docs/screenshots/mesh-inspector.png) |

---

## Getting started

### Requirements

- Python 3
- Pygame (the only runtime dependency)

RenderX was verified with Python 3.12 and Pygame 2.6.1.

### Install and run

```bash
git clone https://github.com/harshmahashabde28/RenderX.git
cd RenderX
pip install -r requirements.txt
python main.py
```

### Run the tests

```bash
# Linux / macOS
SDL_VIDEODRIVER=dummy python -m unittest discover -s tests

# Windows (PowerShell)
$env:SDL_VIDEODRIVER="dummy"; python -m unittest discover -s tests
```

The tests run without opening a window. The final source passes all 86 tests.

---

## Controls

Every action is also available as an on-screen button. Keyboard shortcuts remain for fast use.

| Action | Keys / mouse |
|---|---|
| Switch mode | Click a tab, `F1`–`F7`, or `Tab` to cycle |
| Rotate X / Y | Arrow keys, or left-drag |
| Rotate Z | `Q` / `E`, or right-drag |
| Move | `W` `A` `S` `D`; `Page Up` / `Page Down` for nearer / farther; `Shift` + left-drag or middle-drag to pan |
| Scale | `+` / `-` or mouse wheel |
| Select model | `1` `2` `3` (original three), `N` / `B` (next / previous), or click a model button |
| Load sample OBJ | `O` |
| Projection | `P` |
| Axes | `X` |
| Select vertex | `,` / `.` |
| Pipeline stage | Click a row, or `[` / `]` |
| Compare guides | `V` |
| Lessons | `Enter` next; `H` show answer; `U` / `J` move the clipping edge |
| Quiz | `J` / `K` choose; `Enter` check; `H` hint; `T` retry |
| Guided demo | `F7` to start; `Enter` / `Space` to advance; `F1` to leave |
| Screenshot | `F12` |
| Reset | `R` |
| Exit | `Esc` or close the window |

---

## How it works

For every frame, each vertex goes through this path:

```text
original -> scale -> rotate X -> rotate Y -> rotate Z -> translate -> camera-relative -> clip -> project -> draw
```

- **Model data:** a `Mesh` holds `(x, y, z)` vertices and `(start, end)` edge indices. Original vertices are never modified; the pose is recalculated every frame.
- **Transformations:** scale, then rotate about X, Y and Z, then translate.
- **Perspective:** `screen_x = cx + f*x/z`, `screen_y = cy - f*y/z`
- **Orthographic:** `screen_x = cx + k*x`, `screen_y = cy - k*y`
- **Clipping:** edges crossing the near plane are shortened using `t = (near_z - A.z) / (B.z - A.z)` and `I = A + t*(B - A)`, before the depth division happens.

Coordinate convention: X right, Y up, positive Z away from the camera.

### Architecture

```text
Keyboard / Mouse -> Input Handling -> Scene / State -> Model + Transforms
                 -> Near-plane Clipping -> 3D Projection -> Renderer -> Pygame Display
```

Pure mathematics lives in `transform.py`, `camera.py`, `clipping.py`, `pipeline.py` and `experiments.py`. Pygame drawing lives in `renderer.py`, `axes.py`, `ui.py`, `lab.py` and `dashboard.py`. Keyboard, mouse and dashboard clicks all call the same Scene actions.

---

## Project structure

```text
RenderX/
├── main.py                 entry point
├── requirements.txt        Pygame dependency
├── README.md
├── assets/models/house.obj sample OBJ model
├── docs/screenshots/       images used in this README
├── renderx/
│   ├── app.py              lifecycle and frame loop
│   ├── config.py           colours, sizes, limits
│   ├── mesh.py             Mesh validation and inspection
│   ├── models.py           cube, pyramid, rectangular prism
│   ├── shapes.py           procedural shape library
│   ├── scene.py            pose and shared actions
│   ├── transform.py        scale, rotations, translation
│   ├── camera.py           camera-relative points and projections
│   ├── clipping.py         near-plane edge clipping
│   ├── renderer.py         wireframe drawing
│   ├── axes.py             world axes
│   ├── obj_loader.py       safe OBJ subset loader
│   ├── screenshots.py      timestamped PNG export
│   ├── input.py            keyboard and mouse handling
│   ├── ui.py               information panel and overlays
│   ├── learning.py         mode and selection state
│   ├── pipeline.py         eight-stage vertex snapshots
│   ├── comparison.py       perspective vs orthographic panes
│   ├── curriculum.py       lessons and quiz
│   ├── experiments.py      clipping and operation-order maths
│   ├── lab.py              lesson, mesh, quiz and demo screens
│   ├── dashboard.py        clickable interface
│   └── window.py           screen fit and mouse mapping
├── tests/                  86 automated tests
└── tools/render_qa.py      reproducible static QA frames
```

---

## OBJ support

The loader reads `v` (vertex) lines and `f` (polygon face) lines with positive indices. Optional `v/vt`, `v//vn` and `v/vt/vn` suffixes are accepted and ignored. The model is centred and scaled so its longest side is two world units.

Not supported: negative indices, materials, textures, curves and standalone line records. Files over 2 MB, 20,000 vertices or 50,000 unique edges are rejected. If loading fails, the previous model stays active.

---

## Data and storage

RenderX works with in-memory model data and does not use a database, backend server, cloud or AI service. Screenshots are saved as PNG files. Lesson, quiz and demo progress is kept in memory and resets when the program closes.

---

## Limitations

- Wireframe only: no filled polygons, lighting, textures, hidden-surface removal or depth buffer
- Fixed camera (no free-fly camera)
- Shape parameters are function arguments in `shapes.py`, not on-screen sliders
- The dashboard scales proportionally but has no separate mobile layout
- Automated tests run headless; behaviour and performance on your own machine are best checked by running the app

---

## Development history

| Version | Main change | Tests |
|---|---|---|
| 1 | Cube, pyramid, prism; transforms; perspective; keyboard and mouse; HUD | 24 |
| 2 | Orthographic mode, axes, OBJ loading, near-plane clipping, screenshots | 41 |
| 3 | Learning Laboratory: pipeline inspector, compare views, 15 models, shape details, lessons, quiz, guided demo, clickable dashboard, screen fit | 86 |

---

## Author

Built by [@harshmahashabde28](https://github.com/harshmahashabde28) as a college project (Milestone 03: Implementation / Development).
