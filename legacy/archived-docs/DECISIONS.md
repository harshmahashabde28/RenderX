# RenderX Architecture & Design Decision Records

This document maintains the historical record of architectural decisions made throughout the lifecycle of RenderX. Earlier decisions (D01–D14) are preserved for context, with amendments and superseding decisions explicitly annotated.

---

## Historical Decisions (D01 – D14)

### D01: Foundation on Python 3 and Pygame
- **Decision:** Use Python 3 and Pygame as the primary engine substrate.
- **Rationale:** Pygame provides cross-platform window management, reliable event polling, audio mixing, and 2D blitting while keeping code accessible and readable for education.
- **Status:** Active.

### D02: Pure Software Wireframe Rendering
- **Decision:** Hand-craft all 3D mathematics (vector transforms, rotations, camera projections, clipping) without calling into GPU graphics APIs (OpenGL/Vulkan/DirectX) for the core engine.
- **Rationale:** The educational goal of RenderX is to make the graphics pipeline transparent and inspectable.
- **Status:** Active.

### D03: Non-Destructive Mesh Transformations
- **Decision:** Mesh vertices stored in models must remain immutable during scene manipulation. Every frame recalculates world coordinates afresh from original model coordinates.
- **Rationale:** Prevents cumulative floating-point precision drift and ensures predictable resetting.
- **Status:** Active.

### D04: Bounded Frame Delta and Fixed Timestep
- **Decision:** Clamp delta time $\Delta t \le 0.05$ s (20 FPS minimum tick rate) with a 60 FPS target cap.
- **Rationale:** Prevents physics tunnelling and coordinate explosion during window dragging or temporary freezes.
- **Status:** Active.

### D05: Ephemeral Application State (No Database / No Persistence)
- **Decision:** RenderX runs entirely in-memory with zero local persistence. Progress, high scores, and settings reset on close.
- **Status:** **Amended by D15**. While "no database server or network backend" remains strictly true, local JSON files are now used for settings, floor saves, and learning progress.

### D06: 3D Near-Plane Segment Clipping
- **Decision:** Implement parametric edge clipping $t = (\text{near} - A.z) / (B.z - A.z)$ against the camera near plane.
- **Rationale:** Prevents division by zero or negative depths from projecting inverted vertices across the screen.
- **Status:** Active.

### D07: Safe OBJ Parser with Resource Bounds
- **Decision:** Enforce hard bounds on imported `.obj` files: max 2 MB size, max 20,000 vertices, max 50,000 edges, with unit normalization.
- **Rationale:** Protects against unbounded memory consumption and system hang when parsing untrusted files.
- **Status:** Active.

### D08: Dual Input Scheme (Mouse + Keyboard Parity)
- **Decision:** Every camera and scene action must be operable via both keyboard shortcuts and mouse interactions.
- **Rationale:** Broad accessibility for all desktop users.
- **Status:** Active.

### D09: Avoid NumPy in Core Pipeline
- **Decision:** Do not require or import NumPy for core transformations; write pure Python nested loops and tuples.
- **Status:** **Superseded by D16**. NumPy is now supported as an optional vectorized acceleration path, with the pure-Python reference kept as the authoritative source of truth.

### D10: Single-Window Desktop Experience
- **Decision:** Host all modes inside one unified application window with responsive layout.
- **Status:** Active.

### D11: Headless Testability
- **Decision:** The entire application and all mathematical modules must execute and pass tests headlessly under `SDL_VIDEODRIVER=dummy`.
- **Rationale:** Enables continuous integration across Linux and Windows without hardware displays.
- **Status:** Active.

### D12: Collision-Free Local PNG Screenshots
- **Decision:** Export timestamped screenshots (`screenshots/renderx-YYYYMMDD-HHMMSS.png`) without overwriting previous captures.
- **Status:** Active.

### D13: Integrated Learning Laboratory
- **Decision:** Bundle the 8-stage pipeline inspector, compare views, mesh topology analysis, curriculum lessons, and interactive quiz alongside the 3D viewer.
- **Status:** Active.

### D14: Shared Command Action Layer
- **Decision:** User interface widgets, keyboard hotkeys, and mouse gestures must delegate to the same shared action routines.
- **Status:** Active.

---

## RenderX v4 Architecture Decisions (D15 – D26)

### D15: Local JSON File Persistence (Amends D05)
- **Decision:** Add local JSON file persistence for user settings, auto-saves in *RenderX: Depths*, high scores, and learning progress. Files are stored in the platform standard user config directory (`%APPDATA%/RenderX` on Windows; `$XDG_CONFIG_HOME/renderx` or `~/.config/renderx` on POSIX).
- **Rationale:** Solves the major criticism that user progress, settings, and scores were lost upon application exit. No external database, service, or network connection is introduced.
- **Status:** Active.

### D16: Dual Math Execution Path (Supersedes D09)
- **Decision:** Retain the pure-Python linear algebra implementation as the primary readable reference, but introduce an optional vectorized NumPy path (`fast_math.py`) when NumPy is installed.
- **Rationale:** Allows high edge-count dungeon rendering to maintain $\ge 60$ FPS while keeping the code 100% runnable on pure Python with zero third-party C extensions.
- **Equivalence Requirement:** Both paths must pass the exact same unit tests and parity checks.
- **Status:** Active.

### D17: Dual Camera Architecture: Free First-Person & Fixed Orbit
- **Decision:** Expand `Camera` to support full 6-DOF first-person navigation (position $\vec{P} = (x, y, z)$, yaw $\theta$, pitch $\phi$) for *RenderX: Depths*, while preserving the legacy fixed-camera mode with identical origin offsets for the Learning Laboratory and Explore views.
- **Rationale:** Ensures complete backwards compatibility with known-answer tests in `test_core.py` and `test_learning.py` while providing modern FPS traversal in the dungeon game.
- **Status:** Active.

### D18: Native-Resolution UI System (Replaces Dual-Panel Bitmap Scaling)
- **Decision:** Retire the legacy `ui.Panel` and `dashboard.Dashboard` bitmap cropping/scaling. Implement an in-house native-resolution layout engine (`renderx/ui/layout.py`) using design tokens, flex containers, and DPI-aware scaling.
- **Rationale:** The legacy system rendered into an 1120×740 surface, cropped it with `subsurface((0, 0, 820, 740))`, and scaled it by 0.8 onto a 1360×900 canvas, causing blurred text and wasted draw cycles. The new system renders text and widgets crisply at native display resolutions.
- **Status:** Active.

### D19: First-Person Software Wireframe Game (*RenderX: Depths*)
- **Decision:** Retire the separate OpenGL 3.3 prototype ("Breakpoint") into `legacy/shooter/`. Build the premier game pillar—*RenderX: Depths*—entirely within RenderX's software-rendered wireframe pipeline.
- **Rationale:** Reinforces the project identity: RenderX is a software 3D engine. Demonstrating a fast, responsive first-person shooter running on hand-crafted Python math proves the engine's capability far better than delegating to an external OpenGL shader pipeline.
- **Status:** Active.

### D20: Procedural Waveform Audio Synthesis
- **Decision:** Synthesize all sound effects (laser pulse, scatter blast, explosion, footstep, pickup chime, hurt grunt) and a subtle ambient dungeon drone at runtime using Python math (`math.sin`, frequency ramps, pseudo-random noise) written to 16-bit PCM byte arrays via `pygame.mixer.Sound`.
- **Rationale:** Zero external audio files required, ensuring instant loading, zero asset licensing ambiguities, and tiny repository footprint.
- **Status:** Active.

### D21: 2D Viewport Line Clipping (Liang-Barsky / Cohen-Sutherland)
- **Decision:** Add hand-written 2D screen-edge line clipping following 3D near-plane clipping.
- **Rationale:** Vertices that pass the near-plane test but have coordinates extending thousands of pixels offscreen can trigger severe performance degradation or coordinate overflow inside windowing subsystems. 2D viewport clipping guarantees coordinates sent to `pygame.draw.line` are bounded strictly within viewport rectangles.
- **Status:** Active.

### D22: Depth Cueing via Distance-Based Intensity Fading
- **Decision:** Implement distance attenuation where line brightness scales from full intensity to subtle ambient color over a configurable range $[z_{\text{start}}, z_{\text{far}}]$.
- **Rationale:** Provides strong visual depth and spatial ordering to wireframe scenes without requiring expensive depth-buffering or polygon sorting.
- **Status:** Active.

### D23: Provably Solvable Procedural Mazes
- **Decision:** Every dungeon floor generated in *RenderX: Depths* must undergo automated BFS validation to prove paths exist from Player Spawn $\to$ Security Key $\to$ Floor Exit. If unreachable, generation restarts deterministically with a new seed.
- **Rationale:** Guarantees no unwinnable floors are ever served to the player.
- **Status:** Active.

### D24: In-Game Living Educational Diagnostics
- **Decision:** Introduce the "Engine X-Ray" overlay and "How You See It" vertex inspector directly into the gameplay loop of *RenderX: Depths*.
- **Rationale:** Connects the educational mission of RenderX directly to the playable game. Players can freeze combat and trace the exact mathematical journey of an enemy vertex from local mesh coordinates to final screen pixel.
- **Status:** Active.

### D25: Dependency Minimization
- **Decision:** Allow only `pygame>=2.6.0` as mandatory runtime dependency. `numpy>=2.0.0` is optional (`extras = fast`). Standard library only for persistence, math, logging, and audio buffer generation.
- **Status:** Active.

### D26: Solid Mode Optimization Scope
- **Decision:** Keep Wireframe as the primary, default, and optimized aesthetic. Provide an optional Solid flat-shading mode using Painter's algorithm face depth sorting, but ensure it gracefully falls back to Wireframe if face count exceeds 1,500 on lower-tier hardware.
- **Status:** Active.
