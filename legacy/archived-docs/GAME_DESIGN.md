# RenderX: Depths — Game Design Document & Reference Study

## 1. Reference Analysis (3D RPG Shooter Inspiration)

A thorough structural and mechanical review of the reference project (`3D-RPG-Shooter`) was conducted. The reference is a third-person / top-down survival arena shooter powered by OpenGL 3.3, PyOpenGL, PyGLM, and textured glTF binary (`.glb`) assets. 

### Key Architectural Patterns Learned
- **Finite State Machine Flow:** Distinct lifecycle states (`SPLASH_SCREEN`, `MAIN_MENU`, `DIFFICULTY_MENU`, `GAMEPLAY`, `PAUSED`, `GAME_OVER`) managed cleanly with linear transitions, fade timings, and state reset hooks.
- **Entity Lifecycle:** Compact entity classes (`Player`, `Enemy`, `Projectile`, `Box`, `Loot`) with clean separation of physics updates, bounding collision, lifespan timers, and draw passes.
- **Responsive Aiming & Weapon Mechanics:** Screen-to-world raycasting calculates intersection with the gameplay plane to align weapons and spawn directional projectiles with fire-rate cooldowns.
- **Feedback & Juice:** Immediate visual feedback via hit color flashes, damage numbers, screen shake, and responsive HUD bars for health and ammo.
- **Difficulty & Persistence:** Tiered difficulty profiles (Easy/Normal/Hard) governing spawn density, enemy speed, and damage, alongside atomic JSON persistence for high scores.

### Why RenderX Diverges from the Reference
1. **Software Rendering vs. OpenGL:** The reference relies entirely on GPU shaders, fixed OpenGL pipeline matrices, and hardware buffers. RenderX is strictly software-rendered using hand-crafted Python linear algebra and Pygame 2D primitives.
2. **First-Person Perspective:** Rather than an overhead camera with a player avatar model, *RenderX: Depths* puts the player directly into a first-person wireframe perspective inside procedural subterranean corridors.
3. **Procedural Grid Maze vs. Bounded Box Arena:** The reference uses a static square arena surrounded by four static walls. *RenderX: Depths* generates full multi-room dungeon floorplans with guaranteed exit paths, doors, keys, and spatial culling.
4. **Educational Core:** Unlike a standalone arcade shooter, *RenderX: Depths* integrates the engine's educational mission into combat: live X-ray overlays, viewport clipping diagnostics, and instantaneous pipeline stage inspections for in-world targets.

---

## 2. Core Game Loop: *RenderX: Depths*

```
[Enter Floor] ──> [Explore & Map Maze] ──> [Locate Key / Defeat Guardians]
      │                                                     │
      ▼                                                     ▼
[Gain XP & Upgrades] <── [Combat: 3 Weapon Types] <── [Unlock Floor Exit]
      │                                                     │
      └──────────────────> [Descend to Next Floor] <────────┘
```

1. **Floor Entrance:** Player spawns at a designated elevator tile on Floor $N$ with a procedural seed.
2. **Exploration & Navigation:** Navigate 3D wireframe corridors using WASD + mouse look (or keyboard turn). Fog-of-war reveals grid cells on the minimap as they enter line of sight.
3. **Encounter & Combat:** Encounter patrolling or alerted wireframe enemies (Drones, Sentinels, Brutes, and Floor Bosses). Engage using Pulse Pistol, Scatter Burst, or Arc Launcher.
4. **Key Collection & Progression:** Retrieve the security key to unlock the exit door. Collect medkits, shields, and ammo caches.
5. **Level-up Upgrades:** Defeating enemies grants XP. Reaching level thresholds pauses for a 3-choice upgrade card (damage, fire rate, sprint speed, max shield, ammo capacity).
6. **Floor Descent:** Reaching the unlocked exit triggers an auto-save and descends to Floor $N+1$, where maze complexity, enemy density, and hazards escalate.

---

## 3. World Generation & Provable Solvability
- **Grid Architecture:** 2D grid partitioned into corridors and carved rooms.
- **Algorithm:** Randomized Depth-First Search (Recursive Backtracker) merged with cellular room carving to avoid monotonous single-tile tunnels.
- **Provable Solvability:** Before a floor is committed, a Breadth-First Search (BFS) pathfinder asserts that:
  1. A walkable path exists from `Spawn` to `Key`.
  2. A walkable path exists from `Key` to `Exit`.
  If unreachable, the floor is discarded and regenerated under the next deterministic seed offset.
- **Seeded Runs:** Passing `--seed <value>` reproduces identical floor layouts, enemy spawns, and pickup placements for competition and automated testing.

---

## 4. First-Person Movement & Physics
- **Free Camera:** Camera state maintains world position $\vec{P} = (x, y, z)$ and viewing angles $(\text{yaw}, \text{pitch})$. Forward and strafe vectors are derived from trigonometry.
- **Collision:** Continuous AABB circle-to-box collision against grid walls. Wall sliding allows smooth traversal along surfaces rather than sticky stopping.
- **Controls:** Dual support for Mouse Look + WASD and Keyboard-Only (Arrow keys for turning, WASD/QE for translation).

---

## 5. Arsenal & Combat Mechanics
1. **Pulse Pistol:** Precise single-shot energy weapon. Instant raycast hit detection with a momentary visible energy tracer line. High accuracy, moderate fire rate, infinite basic battery.
2. **Scatter Burst:** Multi-pellet close-range blast. Spreads 5 raycast vectors across a tight cone. High burst damage, uses energy clips.
3. **Arc Launcher:** Fires a physical 3D wireframe projectile undergoing ballistics/travel time. Deals area-of-effect damage on wall or enemy impact.
- **Hit Feedback:** Enemies flash bright white/red upon taking damage; floating wireframe damage numbers ascend and fade; optional screen recoil and camera punch.

---

## 6. Enemy Archetypes & AI State Machine
All enemies are rendered from custom geometric 3D wireframe meshes:
1. **Drone (Fast Harasser):** Octahedral wireframe with spinning rotor edges. High speed, low health, tries to close distance and ram or fire quick burst shots.
2. **Sentinel (Stationary/Ranged):** Prismatic turret chassis with rotating eye pyramid. Fires long-range energy bolts when line-of-sight is achieved.
3. **Brute (Armored Heavy):** Heavy hexagonal prism frame. Slow movement, high hit points, launches heavy explosive arc projectiles.
4. **Nexus Boss (Floor 5/10):** Multi-layered compound mesh (torus + core tetrahedron) with phase-based attacks.

**AI State Machine:**
- `IDLE`: Resting or rotating in patrol zone.
- `PATROL`: Waypoint navigation along corridor nodes.
- `CHASE`: Direct approach using line-of-sight tracking and grid DDA raycast visibility.
- `ATTACK`: Maintaining firing distance and triggering weapon bursts.
- `FLEE`: Backpedaling when below 25% health to seek cover.

---

## 7. Educational Twist: The Living Engine
- **Engine X-Ray Mode (`F8` or HUD button):** Toggles live in-game diagnostics:
  - Bounding wireframes around active entities.
  - Active vertex indices on nearby walls.
  - Near-plane clipping lines highlighted in bright green.
  - Live statistics: Visible vertices, tested edges, clipped edges, edges/second, render time (ms).
- **"How You See It" Target Inspector:** Crosshair lock-on allows pressing `V` to open an overlay freezing the targeted vertex and displaying its exact transformation pipeline stages from model coordinates $(x,y,z)$ to camera space, clipping status, and screen pixel $(cx, cy)$.
- **Live Lens Manipulation:** Real-time toggling between Perspective and Orthographic projection during dungeon exploration, demonstrating depth convergence and focal length ($f$) scaling.
