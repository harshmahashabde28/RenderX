# RenderX

RenderX is a desktop 3D graphics project with four destinations: a renderer
workspace, projection challenges, a three-stage maze campaign, and **Breakpoint**,
a third-person survival shooter.

## Demonstration flow

1. Start in Breakpoint, choose a difficulty, and survive its escalating waves.
2. Return to RenderX and use Explore to rotate a mesh and compare wireframe,
   hidden-line, solid, and depth views.
3. Open Challenges to demonstrate orientation, depth, and near-plane clipping.
4. Complete the Maze campaign by finding keys and reaching each exit.

## Implementation

Explore, Challenges, and Maze use RenderX's Python transformation, clipping,
projection, and software drawing code. Breakpoint runs a separate OpenGL 3.3
pipeline using credited glTF models. It provides mouse aiming, input-driven fire,
collision-aware movement, destructible cover, health supplies, difficulty
profiles, endless waves, scoring, saved best runs, and resize-safe aiming.

The app uses a light pastel palette by default. Its dark palette can be selected
from the navigation bar and is saved in the user's local application data.
