# RenderX

A beginner-friendly 3D wireframe rendering engine built from scratch using Python and Pygame.

## Overview

RenderX demonstrates the fundamentals of a 3D graphics pipeline using plain Python, mathematics, and Pygame for the window, input, and 2D drawing.

The project renders 3D geometry as wireframes and applies transformations and projection to convert 3D coordinates into 2D screen coordinates.

## Features

- Cube, square pyramid, and rectangular prism
- Rotation on X, Y, and Z axes
- Translation on X, Y, and Z axes
- Uniform scaling
- Perspective projection
- Basic keyboard controls
- **OBJ model loading**
- Rendering of loaded OBJ geometry as wireframes
- Simple model centering and normalization

## How It Works

RenderX follows a basic 3D rendering pipeline:

```text
3D Model
   ↓
Vertices & Edges
   ↓
3D Transformations
   ↓
Camera Coordinates
   ↓
Perspective Projection
   ↓
2D Screen Coordinates
   ↓
Wireframe Rendering
```

For built-in objects, the vertex and edge data is defined directly in the program.

For OBJ models, RenderX reads vertex and face information from an `.obj` file and converts the geometry into the same internal representation used by the renderer.

## OBJ Model Loading

RenderX can load a basic OBJ model from the project assets.

The OBJ loader processes:

- Vertex (`v`) definitions
- Face (`f`) definitions
- Polygonal faces
- Common face formats such as `v`, `v/vt`, `v//vn`, and `v/vt/vn`
- Shared edges

Loaded models are converted into wireframe geometry and passed through the same transformation and projection pipeline as the built-in shapes.

The model is centered and normalized before rendering so that it can be displayed consistently within the scene.

## 3D Transformations

Each object is represented using 3D coordinates.

The renderer applies:

```text
Scaling
   ↓
Rotation
   ↓
Translation
   ↓
Projection
```

Rotations use sine and cosine calculations around the X, Y, and Z axes.

Translation changes the object's position in 3D space, while scaling changes its size.

## Projection

RenderX currently uses perspective projection.

Perspective projection makes objects appear smaller as their distance from the camera increases.

Conceptually:

```text
screen_x = center_x + focal_length × x / z
screen_y = center_y - focal_length × y / z
```

This converts 3D coordinates into coordinates that can be drawn on the 2D Pygame window.

## Project Structure

```text
RenderX/
├── main.py
├── renderx/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── mesh.py
│   ├── models.py
│   ├── scene.py
│   ├── transform.py
│   ├── camera.py
│   ├── obj_loader.py
│   └── renderer.py
├── assets/
│   └── models/
├── tests/
├── requirements.txt
└── README.md
```

The exact structure may continue to evolve as the renderer gains additional capabilities.

## Technologies

- Python
- Pygame
- Python `math`
- Python standard library

No external 3D engine is used.

## Installation

Create a virtual environment and install the required dependency:

```bash
python -m venv .venv
```

### Windows

```bash
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

## Controls

| Action | Control |
|---|---|
| Rotate X | Arrow keys |
| Rotate Z | Q / E |
| Move | W / A / S / D |
| Scale | + / - |
| Select built-in shapes | 1 / 2 / 3 |
| Load OBJ model | O |
| Reset | R |
| Exit | Esc |

## Project Goal

RenderX is being developed as a learning project to understand how a basic 3D renderer works internally.

Rather than relying on a ready-made 3D engine, the project implements the core concepts directly:

- 3D coordinate systems
- Mesh representation
- Transformations
- Camera-relative coordinates
- Perspective projection
- OBJ geometry parsing
- 2D wireframe rendering

The project is being developed incrementally, with each stage adding new rendering concepts and capabilities.