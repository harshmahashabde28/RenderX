# RenderX

### A 3D Wireframe Rendering Engine Built from Scratch Using Python and Pygame

RenderX is a lightweight 3D wireframe rendering engine developed from scratch using **Python and Pygame**.

The project demonstrates the basic 3D rendering pipeline by representing objects as vertices and edges, applying 3D transformations, projecting the transformed coordinates onto a 2D screen, and drawing the resulting wireframe in real time.

This is the **first working version of RenderX** and serves as the foundation for all later versions of the project.

---

## Version 1

**Version:** 1.0 / Checkpoint 1  
**Window:** 1120 × 740  
**Language:** Python  
**Graphics Library:** Pygame  
**Tests:** 24 automated tests

---

## What RenderX Can Do

The first version provides a complete small interactive wireframe renderer.

### Built-in 3D Models

RenderX includes three basic wireframe models:

- Cube
- Pyramid
- Rectangular Prism

Each model is represented using:

- 3D vertices
- Indexed edges

The original model geometry is preserved while transformations are calculated from the original coordinates each frame.

---

## 3D Transformations

RenderX performs the main geometric transformations directly in Python.

### Rotation

Objects can be rotated around all three axes:

- X-axis
- Y-axis
- Z-axis

### Translation

Objects can be moved in 3D space along their position coordinates.

### Scaling

Objects can be uniformly enlarged or reduced.

---

## Perspective Projection

The renderer converts 3D coordinates into 2D screen coordinates using **perspective projection**.

Points farther from the camera appear smaller, allowing the wireframe to visually represent depth.

The basic rendering pipeline is:

```text
3D Model
   ↓
Scale
   ↓
Rotate X
   ↓
Rotate Y
   ↓
Rotate Z
   ↓
Translate
   ↓
Perspective Projection
   ↓
2D Screen Coordinates
   ↓
Draw Edges with Pygame
```

The actual 3D calculations are performed by RenderX rather than by a 3D engine.

---

## Interaction

The first version supports both keyboard and mouse interaction.

### Keyboard Controls

| Key | Action |
|---|---|
| `1` | Select Cube |
| `2` | Select Pyramid |
| `3` | Select Rectangular Prism |
| Arrow Keys | Rotate around X/Y |
| `Q / E` | Rotate around Z |
| `W / A / S / D` | Move the object |
| `Page Up / Page Down` | Move object in depth |
| `+ / =` | Increase scale |
| `-` | Decrease scale |
| `R` | Reset transformation |
| `Esc` | Exit |

### Mouse Controls

| Input | Action |
|---|---|
| Left Mouse Drag | Rotate X/Y |
| Right Mouse Drag | Rotate Z |
| `Shift` + Left Drag | Move/Pan |
| Middle Mouse Drag | Move/Pan |
| Mouse Wheel | Scale |

The application also includes on-screen controls and a small HUD showing information about the current scene.

---

## Architecture

The first version follows a simple rendering architecture:

```text
             User Input
                 ↓
          Application Loop
                 ↓
             Scene State
                 ↓
        Transformation System
                 ↓
         Camera / Projection
                 ↓
             Renderer
                 ↓
          Pygame Window
```

### Main Components

**Application**

Controls the main Pygame loop, initialization, updates and shutdown.

**Input**

Processes keyboard and mouse interaction and converts user actions into scene changes.

**Scene**

Stores the currently selected model and its transformation state.

**Mesh / Model Data**

Stores vertices and edges describing the wireframe geometry.

**Transformation System**

Performs scaling, X/Y/Z rotation and translation.

**Camera**

Converts 3D coordinates into 2D screen coordinates using perspective projection.

**Renderer**

Draws the projected edges as lines using Pygame.

---

## Core Rendering Concept

RenderX does not use a ready-made 3D engine.

Instead, the project follows the basic idea:

```text
Vertices + Edges
       ↓
3D Transformations
       ↓
Camera Projection
       ↓
2D Points
       ↓
Connected Lines
```

For every frame, the renderer starts from the original model coordinates and calculates the transformed position of the object again.

This prevents repeated transformations from permanently modifying the original mesh.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Programming language and mathematical calculations |
| Pygame | Window, input handling and 2D line rendering |
| Python `math` | Rotation and projection calculations |
| VS Code | Development environment |
| Git / GitHub | Source-code version control |

RenderX is designed to run locally and does not require a server, database, API or internet connection.

---

## Project Scope

The first version intentionally focuses on the fundamental wireframe rendering pipeline.

### Included

- 3D vertex and edge representation
- Cube, pyramid and rectangular prism
- X/Y/Z rotation
- Translation
- Uniform scaling
- Perspective projection
- Real-time rendering
- Keyboard controls
- Mouse controls
- Model switching
- Reset functionality
- HUD / controls panel
- Automated testing

### Not Included

The following were intentionally outside the scope of this first version:

- Textures
- Lighting
- Shadows
- Materials
- Filled polygon rendering
- OpenGL or another GPU rendering backend
- Physics
- Collision systems
- Full scene editor
- Advanced camera systems
- Large external model pipelines
- OBJ model loading
- Orthographic projection
- Near-plane clipping
- Educational laboratory features

These limitations define the boundary of the original RenderX release and were later addressed selectively in subsequent versions.

---

## Testing

The first working version contains **24 automated tests** covering the core functionality.

Testing focused on areas such as:

- Transformation mathematics
- Projection behaviour
- Model geometry
- Input handling
- Scene state
- Scaling limits
- Reset behaviour
- Rendering-related safety

The automated tests provide a repeatable way to verify the mathematical and programmatic behaviour of the renderer.

A separate physical laptop test is also required for verifying actual keyboard, mouse and display behaviour.

---

## Running RenderX

### Requirements

- Python 3
- Pygame

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Run Tests

```bash
python -m unittest discover -s tests -v
```

---

## Project Goal

The goal of RenderX is not to compete with full graphics engines.

The purpose of the project is to make the fundamental stages of 3D rendering understandable by implementing them directly.

Instead of hiding the mathematics behind a high-level 3D framework, RenderX exposes the basic process:

```text
Model
  ↓
Transformation
  ↓
Projection
  ↓
Rendering
```

This makes the project suitable for learning, experimentation and explaining the underlying mathematics during an academic demonstration or viva.

---

## Version 1 → Foundation

This version established the core architecture that later versions of RenderX were built around.

The fundamental components — **mesh data, scene state, transformations, camera projection and rendering** — formed the foundation for the subsequent development of RenderX.

Later versions extended this foundation with additional graphics capabilities and eventually transformed RenderX into the **Learning Laboratory** version.

---

## Project

**RenderX**  
*A 3D Wireframe Rendering Engine Built from Scratch Using Python and Pygame.*

Built as an educational computer graphics project focused on understanding the fundamentals of 3D rendering.