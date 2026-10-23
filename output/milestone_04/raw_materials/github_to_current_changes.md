# GitHub version → current RenderX: change inventory

This note makes the comparison baseline explicit and gives a fuller inventory than the short comparison table in the report.

## Snapshot identifiers

- **GitHub baseline:** public `main`, `972266d8ff9582fbb9f2f81fd65e855cfb635b0a`, 25 September 2026.
- **Current local tree:** `d34e273b5d9699c915589e5429f0bf27e84401da`, 23 October 2026.
- **Comparison method:** source-tree diff and feature/documentation comparison. These snapshots have unrelated Git histories; the local branch does not have the GitHub commit as an ancestor.
- **Scope:** 423 differing paths: 382 added, 26 modified, and 15 removed. This count includes app code, archived/legacy material, screenshots, QA evidence, and the report package; it is not a count of 423 user-facing features.

## What the published GitHub version was

The public README calls the project “3D Wireframe Rendering Engine & Learning Laboratory,” Version 3 / Milestone 03. It describes a from-scratch Python/Pygame renderer with no OpenGL, NumPy, or general 3D engine in its central pipeline. It includes 15 built-in/procedural models, Explore, an eight-stage vertex pipeline inspector, perspective/orthographic comparison, shape details, 14 lessons, a 10-question quiz, and an eight-step guided demo. The baseline README states that 86 tests pass. That number is quoted from the baseline documentation, not produced by running that historical checkout here.

## Current feature delta

| Component | Change from the GitHub snapshot |
|---|---|
| Product experience | Replaced the Learning Laboratory's seven-mode presentation with a landing screen and four destinations: Explore, Challenges, Maze, and Shooter / Breakpoint. The current README and `FEATURES.md` define the shipped behavior. |
| Renderer foundation | Reorganized the source modules and expanded the rendering path, retaining explicit mesh transforms, camera/projection, and clipping while adding software rendering styles including hidden-line, solid, and depth-oriented modes. Added robustness checks for non-positive depth and non-finite screen coordinates. |
| Models and import | Kept the procedural mesh library and added low-poly showcase OBJ files. OBJ loading is bounded (2 MB, 20,000 vertices, 50,000 unique edges) and reports invalid/over-limit inputs while preserving a safe application state. |
| Explore UI | Reworked the interface into a viewport-focused desktop workspace with docks, model previews, transform/projection controls, live status, menus, context actions, file/recent-file support, keyboard help, preferences, responsive sizing, and theme support. |
| Challenges | Added three concise interactive challenges: Shape Match, Depth & Projection, and Clipping Rescue. These use renderer concepts as practical tasks. |
| Maze | Added a three-stage first-person wireframe maze with a seeded layout, keys and locked exit, scan charges, explored minimap, projection switching, score, elapsed time, and saved best score. |
| Breakpoint | Added a separate OpenGL 3.3 survival shooter. This includes menu/difficulty/pause/restart flows, waves, enemy AI and projectiles, cover, pickups, player damage and dash, HUD/minimap, saved score, progressive vehicle/enemy types, buffs, and a boss encounter every fifth wave. |
| Sound and identity | Added a local logo, bundled fonts with license texts, UI/game sound effects, Maze and Shooter music, volume and music-mute controls, and window icon handling. Attribution for adapted shooter code and assets is recorded in the repository. |
| Reliability | Added UI event/focus recovery fixes, projection edge-case protections, minimum-width text handling, recent-file test isolation, and a recorded defect log. |
| Validation | Added or expanded tests for the renderer, UI, challenges, Maze, Shooter, audio, file-open flow, and launch behavior, plus headless scenario, edge-case, resize, and performance runners. |

## Source-tree inventory by area

The path counts below are additions in the tree comparison (382 additions overall). Existing baseline paths were also modified and removed, as summarized above.

| Path group | Added paths | What they contain |
|---|---:|---|
| `renderx/` | 118 | New/refactored application, rendering, UI, challenge, maze, shooter, audio, and support modules. |
| `legacy/` | 61 | Archived earlier UI/game implementation and prior documentation/metadata. This is retained history, not a new runtime feature. |
| `assets/` | 29 | Fonts, audio, logo, and sample/showcase models. |
| `tests/` | 10 | Current test modules added; 5 existing modules also modified and 2 removed. |
| `tools/` | 16 | QA scenarios and runners, benchmark, resize checks, and focused edge verification. One earlier tool was removed. |
| `docs/` | 4 | Architecture, overview, references, and testing documentation. |
| `output/` | 128 | Milestone evidence, screenshots, test-run artifacts, generated report source, and generated PDFs. These are documentation artifacts, not runtime application features. |
| Other root/config paths | 6 added, plus 1 `.github/` workflow | Project instructions and design/convention/feature/bug documentation, plus the new project configuration file. README, entry point, requirements, and other configuration changes are modifications rather than additions. |
| `screenshots/` | 9 added, 6 removed | Updated and additional app evidence. |

The groups sum to the 382 added paths. Modifications and removals affect several of the same groups; directory counts should not be added to the total change count.

## Current design boundary

Explore, Challenges, and the wireframe Maze are centered on RenderX's own software rendering and projection concepts. Breakpoint uses a separate OpenGL 3.3 pipeline because it is a real-time textured shooter. This distinction matters when presenting the project: it is accurate to say that RenderX contains a custom educational renderer and a separate game renderer; it would be inaccurate to imply that Breakpoint is drawn by the software wireframe renderer.

## Verifying the comparison

Use the GitHub repository's commit history and compare the README/source at `972266d8ff9582fbb9f2f81fd65e855cfb635b0a` with the current local tree at `d34e273b5d9699c915589e5429f0bf27e84401da`. The current feature descriptions are in the project `README.md` and `FEATURES.md`; the architecture boundary is in `docs/ARCHITECTURE.md`; the QA findings are in `BUGLOG.md`.
