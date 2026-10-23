# RenderX - Milestone 04: Testing and Validation

## 1. Milestone 04 scope and version boundary

This report continues the three previously submitted RenderX milestones. It does not repeat their project introduction or implementation narrative. It records the transition from the published Learning Laboratory to the current RenderX application, then documents testing, defects, performance evidence, and validation limits for the current version.

The comparison uses GitHub `main` at `972266d8ff9582fbb9f2f81fd65e855cfb635b0a` and the current application snapshot at `d34e273b5d9699c915589e5429f0bf27e84401da`. These source trees have unrelated Git histories, so the report compares their documented features and files rather than presenting them as a single commit lineage.

## 2. Version comparison and development scope

### 2.1 Compared versions

| Version | Identifier | Description |
|---|---|---|
| Public GitHub baseline | `972266d8ff9582fbb9f2f81fd65e855cfb635b0a` | GitHub `main`, dated 25 September 2026; README presents RenderX as a wireframe-rendering Learning Laboratory (Milestone 03). |
| Current local version | `d34e273b5d9699c915589e5429f0bf27e84401da` | Local `v4-showcase` tree, dated 23 October 2026; latest commit records Milestone 04 evidence. |

The public and local trees have unrelated Git histories. Therefore, the comparison below describes the user-visible and source-tree changes between the two snapshots. It does not claim that every current local commit descends from the listed GitHub commit. A tree comparison reports 423 changed paths, with substantial additions, removals, and reorganizations.

### 2.2 What the GitHub version provided

The public README describes RenderX as a Python/Pygame 3D wireframe learning application. It includes a custom rendering pipeline, Explore and educational content, mesh and projection inspection, clipping and comparison views, a guided demonstration, quizzes/lessons, sample models, and an automated suite reported by that README as 86 tests. That test count is the README's claim; the GitHub checkout was not run independently for this report.

### 2.3 What the current version adds or changes

| Area | GitHub baseline | Current local version |
|---|---|---|
| Product structure | Learning Laboratory organized around renderer lessons and demonstrations. | Landing screen and four destinations: Explore, Challenges, Maze, and Shooter / Breakpoint. |
| Core renderer | Wireframe mesh transformation and projection used for graphics learning. | Retains the custom transform, camera, clipping, and projection concepts; adds wireframe, hidden-line, solid, and depth-oriented software rendering modes and an expanded set of procedural meshes. |
| Guided practice | Lessons, comparisons, and quiz-style learning content. | Three focused tasks: Shape Match, Depth & Projection comparison, and Clipping Rescue. |
| Playable demonstration | Guided renderer demonstration and sample scenes. | Three-stage first-person wireframe maze campaign with keys, exit conditions, scan pulse, minimap, projection toggle, score, and saved best score. |
| Additional game | No separate shooter described in the baseline README. | Breakpoint, a separate resizable OpenGL 3.3 survival shooter with escalating waves, enemies, destructible cover, pickups, buffs, vehicle progression, and periodic boss encounters. |
| Application interface | Earlier learning-focused screens. | Workspace-style desktop interface with viewport, panels, status information, menus, shortcuts, preferences, recent files, and light/dark themes. |
| Assets and feedback | Educational model and renderer assets. | Bundled application logo, fonts, audio, demo OBJ models, game assets, and third-party attribution/license records. |
| QA and reliability | Baseline README reports an 86-test suite. | Current tree includes renderer, UI, maze, challenge, shooter, audio, file-open, and launch-flow tests plus resize, edge-case, and headless interaction runners. |

The current version is a broader product than the GitHub learning-laboratory snapshot. Its main technical continuity is the custom educational renderer; its largest product changes are the challenge and game destinations, the redesigned application shell, and a separate OpenGL game pipeline.

### 2.4 Selected local development milestones

| Date | Local milestone |
|---|---|
| 21 Oct 2026 | Reorganized the renderer foundation and introduced software-rendering styles, clipping, culling, and a benchmark path. |
| 21 Oct 2026 | Built the native-resolution UI shell and responsive workspace. |
| 21 Oct 2026 | Integrated Breakpoint, added audio and licensed interface assets, and expanded progression with bosses, vehicles, and buffs. |
| 23 Oct 2026 | Aligned the application with desktop 3D conventions, added landing-first navigation, removed the unwanted landing preference, and added lightweight OBJ showcase models. |
| 23 Oct 2026 | Isolated recent-file test state and recorded the current testing evidence. |

This is a summary of the local branch's recorded milestones, not a complete narrative of every changed path.

## 3. System overview

RenderX is organized into two related 3D experiences.

### 3.1 Explore and Challenges

The main renderer uses Python code for mesh transforms, camera-space operations, clipping, projection, and drawing. Pygame provides the window, input, audio mixer, and 2D drawing surface. Explore supports built-in and imported OBJ meshes, transforms, perspective and orthographic projection, render-mode selection, axes, and a viewport-first inspector layout. Challenges use renderer state to demonstrate orientation, depth/projection differences, and clipping at the near plane.

### 3.2 Maze

Maze is a first-person wireframe campaign with three stages. The player navigates a seeded maze, finds two signal keys, and reaches an exit. An explored minimap and limited scan charges provide navigation feedback. The campaign tracks time and score and stores a best score.

### 3.3 Breakpoint

Breakpoint is a separate OpenGL 3.3 window and rendering path. It adds real-time combat and uses bundled 3D models, textures, and shaders. The run contains escalating waves, enemy projectiles, destructible cover, field supplies, timed boosts, vehicle/enemy progression, and a multi-phase boss encounter every fifth wave. It returns the user to RenderX when the game is exited through its return action. The code and assets adapted from the upstream shooter are acknowledged in the repository's `renderx/shooter/UPSTREAM.md` and license files.

### 3.4 Interface and persistence

The application has a landing screen, destination navigation, menus, contextual help, keyboard shortcuts, file open and recent-file support, preferences, theme switching, volume and music mute controls, and saved user preferences. Fonts and logo artwork are bundled locally. Explore includes a light theme; the current default is dark.

## 4. Environment and tools

| Item | Recorded environment |
|---|---|
| Operating system | Windows 11 Home Single Language, build 10.0.26300 |
| Python | 3.13.15 |
| Pygame | 2.6.1 |
| pytest | 9.1.1 |
| Machine | Lenovo, model 83DV |
| Test mode | Automated tests and headless application runs using SDL dummy video where indicated |

Machine and software information above describes the environment used for the recorded run. It is not a minimum system requirement. Breakpoint requires a compatible OpenGL 3.3 graphics device for native interactive gameplay.

## 5. Test strategy

Validation used several levels:

1. **Unit tests** check math, mesh handling, OBJ parsing, input mapping, UI components, and settings.
2. **Integration tests** check navigation, loading a sample OBJ, challenge flow, maze state, shooter state, audio controls, and file-opening behavior.
3. **Edge-case checks** exercise depth zero/negative values, very large coordinates, non-finite projection results, and positive near-plane clipping.
4. **Interaction scenarios** inject sequences such as opening help, clicking outside, pointer exit, and focus loss, then check the final UI state.
5. **Responsive checks** run the interface at eight window sizes and inject rapid resize events.
6. **Performance runs** measure three five-second headless scenarios: idle Explore, rotating Explore, and a built-in Signal mesh.
7. **Visual evidence** captures the major destinations, representative controls, themes, and two window sizes.

The automated suite and headless scripts do not replace a final manual run on the target computer. The test scope and limitations are stated in Section 8.

## 6. Test results

### 6.1 Automated and focused verification

| Check | Result | Notes |
|---|---:|---|
| Automated suite | **135 passed; 1 warning; 36 subtests passed** | Run after the recent-file state isolation fix. One pending-deprecation warning remains in a shooter dependency (`import glm` in `renderx/shooter/entities/box.py`). |
| Engine edge runner | **12 checks passed** | Includes zero/negative depth rejection, extreme coordinates, infinite focal length, and geometry safety. |
| Resize matrix | **8 sizes passed** | 800×500, 1024×640, 1280×720, 1366×768, 1920×1080, 2560×1440, 1024×1600, 2200×720; also 50 rapid resize events. |
| Headless app screenshots | **15 current scenarios passed** | Destinations, menus, themes, sample OBJ, shortcut overlay, and two representative window sizes. |
| Current defect log | **11 findings recorded and marked fixed/verified**, with per-item exceptions | Includes 8 UI findings, 2 core projection findings, and 1 test-isolation finding. Some platform behavior has a headless verification limit. |

“Passed” means that the indicated automated check completed successfully in the recorded environment. It does not imply that every hardware, driver, or interactive usage combination was tested.

### 6.2 Performance measurements

Each scenario ran for five seconds under the SDL dummy driver. Three hundred frames were recorded per run.

| Scenario | Average frame time | p95 | p99 | Approx. reciprocal of mean frame time |
|---|---:|---:|---:|---:|
| Explore idle | 8.673 ms | 15.084 ms | 16.656 ms | 115.3 frames/s |
| Explore orbit | 8.803 ms | 14.735 ms | 16.421 ms | 113.6 frames/s |
| Built-in Signal mesh | 23.729 ms | 30.725 ms | 34.341 ms | 42.1 frames/s |

The last column is calculated as 1,000 divided by average milliseconds per frame. These are headless software-path measurements and should not be presented as native display or GPU frame-rate guarantees. Breakpoint GPU performance and loading time for a large external OBJ were not measured. The specific external `model.obj` previously discussed is approximately 34.46 MB and exceeds the app's 2 MB import limit, so it was not used as a successful-load performance sample.

### 6.3 Memory measurements

The headless runs recorded a peak working set of approximately 65.0–65.3 MB (about 62 MiB), with a measured delta of roughly 9.8–10.0 MB over the recorded baseline. Treat these as process-level measurements for the test scenarios, not a universal memory requirement or a measurement of a full native OpenGL session.

## 7. Defect handling and retesting

The current `BUGLOG.md` records the following classes of defects and their fixes:

| Finding | Example symptom | Resolution and retest |
|---|---|---|
| Repeated generic mesh mark | Model rows were visually indistinguishable. | Used the RX brand mark and mesh-derived previews; captured destinations. |
| Missing app window identity | Operating system title had no project icon. | Applied a shared icon and title helper; headless icon call verified. |
| Zero-depth projection | A point at depth zero could divide by zero. | Rejects non-positive depth and preserves valid positive near-plane clipping; engine edges rerun. |
| Extreme projected coordinates | Finite input could produce infinite screen coordinates. | Checks projected outputs for finiteness; edge tests rerun. |
| Help overlay input leak | A click under the overlay activated a destination. | Overlay captures and consumes the click; event schedule replayed. |
| Hover/pressed state after pointer/focus loss | UI could look stuck after leaving the window. | Clears transient interaction state; event sequences replayed. |
| Incorrect pointer cursor | Cursor did not indicate buttons, fields, or splitters. | Added cursor requests and verified request sequence; native cursor appearance remains unverified in dummy video. |
| Truncation colliding with compact icon controls | Ellipsis overlapped a button icon. | Omits a label when it cannot fit; minimum-size typography audit rerun. |
| Unsupported ellipsis glyph | Bundled font raised an error when drawing truncation. | Changed truncation mark to ASCII periods; font tests rerun. |
| Recent-file test used real user state | Test depended on earlier app usage. | Resets in-memory recent files inside the isolated test context; full suite rerun. |

The table summarizes findings; the repository's `BUGLOG.md` is the authoritative detailed record, including reproduction steps and verification status. The OpenGL Breakpoint display cannot be created by the SDL dummy driver, so its native display identity and actual gameplay require manual validation.

## 8. Security, robustness, and known limits

The OBJ loader applies a 2 MB file-size limit, 20,000-vertex limit, and 50,000-unique-edge limit. It rejects malformed data, non-finite values, invalid face references, and unsupported negative relative indices rather than evaluating file content as code. The oversized-file scenario checks that an over-limit input produces a controlled error state.

The project did not undergo a formal penetration test or third-party security audit. Testing did not validate every arbitrary OBJ produced by every modeling package. The previously supplied large `model.obj` is over the loader's current size limit and therefore cannot be opened without simplifying or splitting it first.

Headless tests cannot prove the behavior of the Windows native file picker, the actual system cursor, GPU-specific OpenGL rendering, sound playback on physical audio devices, fullscreen behavior on every display, or sustained performance under live user input. These require a manual target-machine acceptance run. The Explore application opens with a default cube, so an empty-scene screenshot was not captured. The evidence set also does not include matched before/after captures for every visual issue described in earlier planning notes.

## 9. Conclusion

Between the published GitHub Learning Laboratory snapshot and the current local project, RenderX grew into a larger desktop graphics application while keeping its custom wireframe renderer as a central feature. The current project adds software rendering modes, guided challenges, a wireframe maze campaign, a separate OpenGL shooter, an expanded interface, and additional audio, visual, and file-handling features.

The available automated evidence shows that the current test suite and targeted headless checks pass in the recorded environment. Projection edge cases, responsive layouts, and representative navigation flows were exercised. The results support the current implementation, subject to a final native Windows acceptance run and the stated limitations. The comparison baseline and commit identifiers are provided so the scope can be reproduced accurately.

## References

1. RenderX public repository, GitHub `main`: https://github.com/harshmahashabde28/RenderX (baseline snapshot `972266d8ff9582fbb9f2f81fd65e855cfb635b0a`, accessed for source comparison 23 October 2026).
2. Current local RenderX source tree, commit `d34e273b5d9699c915589e5429f0bf27e84401da`, 23 October 2026.
3. Current project documentation: `README.md`, `FEATURES.md`, `BUGLOG.md`, `docs/ARCHITECTURE.md`, `docs/TESTING.md`, and `renderx/shooter/UPSTREAM.md`.
4. Python documentation: https://docs.python.org/3/
5. Pygame documentation: https://www.pygame.org/docs/

## Appendix A — Reproduction commands

Run these from the repository root in PowerShell. The project virtual environment should contain the project dependencies.

```powershell
$env:LOCALAPPDATA = Join-Path $env:TEMP 'renderx-m04-test-local'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools\qa\engine_edges.py
.\.venv\Scripts\python.exe tools\qa\resize_matrix.py <temporary-output-folder>
.\.venv\Scripts\python.exe tools\qa\performance_runs.py --seconds 5 --output <temporary-output-folder>
.\.venv\Scripts\python.exe output\milestone_04\source\capture_screenshots.py
```

