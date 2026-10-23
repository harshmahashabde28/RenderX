# Guidelines for AI Coding Agents on RenderX

## 1. Project Philosophy & Core Constraints
- **Educational Clarity First:** RenderX is an educational software 3D engine. Code readability is an explicit design requirement. Write small, well-named functions, explicit types, and docstrings explaining *why* equations work.
- **Pure-Python 3D Core:** Everything inside `renderx/core/` must be pure Python with zero dependencies on Pygame, external math libraries, or GPU acceleration. NumPy may be used only inside optional accelerated engine paths (`fast_math.py`) with a pure-Python reference kept alongside it.
- **No External Game Engines / No OpenGL:** Pygame provides the window, 2D rasterization (lines and polygons), input, and audio mixing. All 3D transformations, viewing projections, near-plane clipping, and culling must remain software-rendered.
- **Shared Action Layer:** UI buttons, keyboard shortcuts, and mouse gestures must call the exact same underlying action commands. Never duplicate business or transformation logic across input listeners.

## 2. Safety, Geometry & Mathematics
- **Depth Safety:** Never divide by zero or negative depths. Points behind or on the near plane ($z \le \text{near}$) must be clipped or rejected before screen projection.
- **Non-Destructive Meshes:** Original mesh vertices are immutable. Always transform from original geometry rather than accumulating matrix mutations in model coordinates.
- **Deterministic Math:** Transformations must strictly adhere to the established pipeline order: $\text{Scale} \to R_x \to R_y \to R_z \to \text{Translate}$. Known-answer tests must remain green.

## 3. Truth in Reporting & Quality Gates
- **Never Invent Results:** Never invent benchmark numbers, FPS metrics, test counts, or hardware capabilities. Report only numbers obtained from running real scripts and tests on the actual machine.
- **Local Git Discipline:** Work on the `v4-showcase` branch. Make one clear conventional commit per phase. Never push, force-push, or rewrite history. Never delete user files; move retired files into `legacy/` with documentation.
- **Headless Compatibility:** Every screen, module, and state must be testable headlessly with `SDL_VIDEODRIVER=dummy`.
