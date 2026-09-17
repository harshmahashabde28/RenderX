# RenderX

A beginner-friendly **3D wireframe rendering engine** built with Python and Pygame.
Explore a cube, square pyramid and rectangular prism using keyboard and mouse.

## Overview

RenderX demonstrates the fundamentals of a 3D graphics pipeline. Pygame supplies
the window, input and 2D drawing; plain Python and `math` supply the 3D calculations.
This is the working MVP for **Milestone 3: Implementation / Development**.
It is an offline desktop application: no database, server, account or API key.

## Features

- Cube (8 vertices / 12 edges), square pyramid (5 / 8), rectangular prism (8 / 12).
- Rotation on X/Y/Z; translation on X/Y/Z; uniform scaling.
- Perspective projection through a fixed camera facing positive Z.
- Keyboard controls, mouse gestures and clickable shape/reset/exit buttons.
- Live transform values, instructions and FPS in a dark control panel.
- Bounded movement/scaling, safe depth checks and focus-loss protection.
- Frame-rate-independent keyboard updates and a nominal 60 FPS frame limit.
- Pygame is the only external dependency; no NumPy or external 3D engine.

## How It Works

**3D model → transformations → camera-relative coordinates → perspective
projection → 2D coordinates → wireframe rendering.**

Each frame starts with original vertices, scales them, rotates around X then Y
then Z, and translates them. Camera position is subtracted. Each vertex is
projected once, then edges are drawn with `pygame.draw.line()`.
Original vertices never change.

## Project Structure

```text
RenderX/
├── main.py                 # Entry point and startup diagnostics
├── renderx/
│   ├── __init__.py
│   ├── app.py              # Window, frame loop and shutdown
│   ├── config.py           # Colours, speeds and safety limits
│   ├── mesh.py             # Vertex/edge container and validation
│   ├── models.py           # Built-in shape data
│   ├── scene.py            # Current pose and shared actions
│   ├── transform.py        # Scale, rotation and translation
│   ├── camera.py           # Camera coordinates and perspective
│   ├── renderer.py         # Project vertices and draw edges
│   ├── input.py            # Keyboard/mouse routing and focus handling
│   └── ui.py               # Status, instructions and buttons
├── tests/
│   ├── test_core.py        # Maths and safety tests
│   └── test_interaction.py # Input, drawing and lifecycle tests
├── requirements.txt
├── .gitignore
└── README.md
```

The ZIP also includes separate `College-Notes/` with test evidence, viva help and
updated project notes. These sit outside the Git repository for use in Obsidian.

## Installation

Extract the ZIP. Open a terminal **inside `RenderX`**, where `main.py` is located.
Use Python 3.10 or newer. Tested with Python 3.12.14 and Pygame 2.6.1 on Linux
using SDL's headless display driver. Interactive use requires a normal desktop.
Physical Windows keyboard/mouse testing is still pending.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

No environment activation is needed. If `py` is unavailable but `python` works,
use `python -m venv .venv` first. In VS Code select `.venv\Scripts\python.exe`
as your interpreter; run through the terminal if Code Runner selects another one.

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

With your intended Python environment already active:

```bash
python -m pip install -r requirements.txt
python main.py
```

After publishing your own repository, you can clone instead of extracting:

```bash
git clone https://github.com/YOUR_USERNAME/RenderX.git
cd RenderX
python -m pip install -r requirements.txt
python main.py
```

Replace `YOUR_USERNAME`; this is a placeholder, not a verified existing remote.

## Controls

| Action | Keyboard | Mouse |
|---|---|---|
| Rotate X | Up / Down | Left-drag vertically |
| Rotate Y | Right / Left | Left-drag horizontally |
| Rotate Z | E / Q | Right-drag horizontally |
| Move up / down | W / S | Shift + left-drag or middle-drag |
| Move left / right | A / D | Shift + left-drag or middle-drag |
| Move nearer / farther | Page Up / Page Down | — |
| Enlarge / shrink | + or equals / minus; numpad supported | Scroll up / down |
| Cube / pyramid / prism | 1 / 2 / 3 | Click shape button |
| Reset current shape | R | Click Reset |
| Exit | Esc | Click Exit or close window |

Hold movement keys; opposite keys cancel. Selecting a shape resets its pose.
Reset retains the selected shape. Gestures start only in the drawing area;
leaving it cancels dragging. Losing focus cancels dragging and pauses key updates.
Wheel input over the panel is ignored.

W/S retain the approved design's vertical movement mapping; Page Up/Down add
depth movement. The camera itself is fixed. X/Y position is bounded to ±1 world
unit, depth to 3.5–10, and scale to 0.3–1.3. Extreme close-ups can extend beyond
the viewport; Reset recovers the default view.

## 3D Mathematics

- **Vertices:** local `(x, y, z)` corner positions.
- **Edges:** index pairs, e.g. `(0, 1)` connects the first two vertices.
- **Scaling:** multiply all coordinates by the same positive number.
- **Rotation:** use sine/cosine. Z rotation gives `x_new = x*cos(a) - y*sin(a)`
  and `y_new = x*sin(a) + y*cos(a)`.
- **Translation:** add the object position after rotating.
- **Camera:** subtract camera position from world coordinates.
- **Perspective:** `screen_x = centre_x + focal_length*x/z` and
  `screen_y = centre_y - focal_length*y/z`. Double depth gives half the offset.
  The minus sign converts upward world Y to downward screen Y.

Angles use radians internally and degrees in the panel. Order matters:
scale → rotate X → rotate Y → rotate Z → translate. Translating before rotation
would rotate the object's position too, making it orbit the origin.

Depth at/below 0.1 and non-finite points return `None`. Edges using these points
are skipped safely. This is rejection, not proper near-plane edge clipping.
All built-in shapes stay beyond the near plane within the supported bounds.
2D drawing is clipped to the viewport to protect the panel. Rear edges remain
visible because hidden-surface removal is outside this wireframe MVP.

## Tests

With the intended environment active, run:

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py renderx tests
```

Or use the explicit virtual-environment Python path from installation.
24 automated tests cover maths, source geometry preservation, safety limits,
keyboard/mouse actions, shape switching, reset, rendering and exit. UI tests use
SDL's dummy driver. Rendered frames for all three shapes were visually inspected;
the real app loop also completed a 60-second scripted interaction run.
These checks do not substitute for physical Windows input testing.

## Technologies Used

Python, Pygame 2.6.1, `math`, `dataclasses`, `unittest`, and Git.
A dataclass groups related values and supplies an initialiser; no class framework
or inheritance hierarchy is needed.

## Git and GitHub

The ZIP includes real staged commits in `.git`. Inspect with `git log --oneline`
and `git status` inside `RenderX`. No remote is configured and nothing was pushed.
Commit authorship identifies the coding agent. Before your own next commit:

```bash
git config user.name "Your Name"
git config user.email "YOUR_VERIFIED_OR_GITHUB_NOREPLY_EMAIL"
```

Create an empty GitHub repository without automatic README/licence/gitignore.
Replace this placeholder URL with its real URL:

```bash
git remote add origin https://github.com/YOUR_USERNAME/RenderX.git
git push -u origin main
```

Push only `RenderX`; `College-Notes` is separate. Do not initialise another
repository in the parent folder. Caches, environments, IDE files and secrets are
ignored. The app itself needs no credentials.

## Future Improvements

OBJ loading, proper near-plane clipping, hidden-surface removal, filled polygons,
lighting, texture mapping, movable camera and resizable window.
