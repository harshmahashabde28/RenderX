"""Procedural first-person wireframe maze built on RenderX's own renderer."""
from collections import deque
from dataclasses import dataclass
import json
from math import cos, hypot, pi, sin, sqrt, tau
import os
from pathlib import Path
from random import Random

import pygame

from renderx import config
from renderx.input_map import MAZE_KEYS, MOUSE_BUTTONS
from renderx.camera import Camera
from renderx.mesh import Mesh

MAZE_SIZE = 11
LEVEL_SIZES = (11, 15, 19)
CELL_SIZE = 2.0
WALL_HEIGHT = 2.4
PLAYER_RADIUS = 0.27
PLAYER_EYE_HEIGHT = 1.05
KEY_RADIUS = 0.26
MOVE_SPEED = 2.7
TURN_SPEED = 2.15


@dataclass(frozen=True)
class MazeBlueprint:
    """A connected, perfect maze and reachable positions for its objectives."""
    size: int
    seed: int
    cells: tuple[tuple[int, ...], ...]
    start: tuple[int, int]
    keys: tuple[tuple[int, int], tuple[int, int]]
    exit: tuple[int, int]

    @classmethod
    def generate(cls, size=MAZE_SIZE, seed=7):
        if type(size) is not int or size < 7 or size % 2 == 0:
            raise ValueError("Maze size must be an odd integer of at least 7.")
        grid = [[1] * size for _ in range(size)]
        start = (1, 1)
        grid[start[1]][start[0]] = 0
        randomizer = Random(seed)
        stack = [start]
        directions = ((0, -1), (1, 0), (0, 1), (-1, 0))

        while stack:
            x, z = stack[-1]
            options = [(x + dx * 2, z + dz * 2, dx, dz)
                       for dx, dz in directions
                       if 1 <= x + dx * 2 < size - 1 and
                       1 <= z + dz * 2 < size - 1 and
                       grid[z + dz * 2][x + dx * 2] == 1]
            if not options:
                stack.pop()
                continue
            nx, nz, dx, dz = randomizer.choice(options)
            grid[z + dz][x + dx] = 0
            grid[nz][nx] = 0
            stack.append((nx, nz))

        open_cells = [(x, z) for z in range(size) for x in range(size)
                      if grid[z][x] == 0]
        from_start = _distances(grid, start)
        first_key = max((cell for cell in open_cells if cell != start),
                        key=lambda cell: from_start[cell])
        from_first = _distances(grid, first_key)
        second_key = max((cell for cell in open_cells
                          if cell not in (start, first_key)),
                         key=lambda cell: from_first[cell])
        from_second = _distances(grid, second_key)
        exit_cell = max((cell for cell in open_cells
                         if cell not in (start, first_key, second_key)),
                        key=lambda cell: from_second[cell])
        return cls(size, seed, tuple(tuple(row) for row in grid), start,
                   (first_key, second_key), exit_cell)

    def is_open(self, cell):
        x, z = cell
        return 0 <= x < self.size and 0 <= z < self.size and self.cells[z][x] == 0

    def cell_center(self, cell):
        return cell_center(cell)

    @property
    def open_cell_count(self):
        return sum(value == 0 for row in self.cells for value in row)


def _distances(grid, start):
    size = len(grid)
    distances = {start: 0}
    queue = deque([start])
    while queue:
        x, z = queue.popleft()
        for dx, dz in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            neighbour = (x + dx, z + dz)
            nx, nz = neighbour
            if (0 <= nx < size and 0 <= nz < size and grid[nz][nx] == 0
                    and neighbour not in distances):
                distances[neighbour] = distances[(x, z)] + 1
                queue.append(neighbour)
    return distances


def cell_center(cell):
    x, z = cell
    return ((x + 0.5) * CELL_SIZE, (z + 0.5) * CELL_SIZE)


@dataclass
class MazeCamera(Camera):
    """Camera that faces +Z at yaw zero and rotates around the Y axis."""
    yaw: float = 0.0

    def relative_point(self, world_point):
        dx = world_point[0] - self.position[0]
        dy = world_point[1] - self.position[1]
        dz = world_point[2] - self.position[2]
        sine, cosine = sin(self.yaw), cos(self.yaw)
        return (dx * cosine - dz * sine, dy,
                dx * sine + dz * cosine)


class _PerspectiveWallVisibility:
    """Precompute first-wall depth per screen column for fast edge queries."""
    def __init__(self, maze, viewport, focal_length):
        self.maze = maze
        self.viewport = pygame.Rect(viewport)
        self.focal_length = focal_length
        self.centre_x = self.viewport.centerx
        sine, cosine = sin(maze.yaw), cos(maze.yaw)
        self.depths = []
        for screen_x in range(self.viewport.left, self.viewport.right + 1):
            camera_slope = (screen_x - self.centre_x) / focal_length
            direction_x = camera_slope * cosine + sine
            direction_z = -camera_slope * sine + cosine
            self.depths.append(self._first_wall_depth(direction_x, direction_z))

    def _first_wall_depth(self, direction_x, direction_z):
        maze = self.maze
        cell_x = int(maze.player_x // CELL_SIZE)
        cell_z = int(maze.player_z // CELL_SIZE)
        step_x = 1 if direction_x > 0 else -1 if direction_x < 0 else 0
        step_z = 1 if direction_z > 0 else -1 if direction_z < 0 else 0
        infinity = float('inf')
        if step_x:
            boundary_x = ((cell_x + 1) * CELL_SIZE if step_x > 0
                          else cell_x * CELL_SIZE)
            max_x = (boundary_x - maze.player_x) / direction_x
            delta_x = CELL_SIZE / abs(direction_x)
        else:
            max_x = delta_x = infinity
        if step_z:
            boundary_z = ((cell_z + 1) * CELL_SIZE if step_z > 0
                          else cell_z * CELL_SIZE)
            max_z = (boundary_z - maze.player_z) / direction_z
            delta_z = CELL_SIZE / abs(direction_z)
        else:
            max_z = delta_z = infinity

        while True:
            next_depth = min(max_x, max_z)
            if abs(max_x - max_z) <= 1e-9:
                if (not maze.blueprint.is_open((cell_x + step_x, cell_z)) or
                        not maze.blueprint.is_open((cell_x, cell_z + step_z))):
                    return next_depth
                cell_x += step_x
                cell_z += step_z
                max_x += delta_x
                max_z += delta_z
            elif max_x < max_z:
                cell_x += step_x
                max_x += delta_x
            else:
                cell_z += step_z
                max_z += delta_z
            if not maze.blueprint.is_open((cell_x, cell_z)):
                return next_depth

    def __call__(self, camera_point):
        camera_x, camera_y, depth = camera_point
        if depth <= 0:
            return True
        screen_x = self.centre_x + self.focal_length * camera_x / depth
        column = min(self.viewport.width,
                     max(0, round(screen_x) - self.viewport.left))
        wall_depth = self.depths[column]
        if depth <= wall_depth + 1e-5:
            return True
        wall_height = PLAYER_EYE_HEIGHT + camera_y * wall_depth / depth
        return wall_height < 0 or wall_height > WALL_HEIGHT


class _MeshBuilder:
    """Join nearby wall panels into a validated, deduplicated line mesh."""
    def __init__(self):
        self.vertices = []
        self.edges = []
        self._indices = {}
        self._edge_set = set()

    def vertex(self, point):
        key = tuple(round(value, 6) for value in point)
        if key not in self._indices:
            self._indices[key] = len(self.vertices)
            self.vertices.append(key)
        return self._indices[key]

    def edge(self, start, end):
        a, b = self.vertex(start), self.vertex(end)
        key = tuple(sorted((a, b)))
        if a != b and key not in self._edge_set:
            self._edge_set.add(key)
            self.edges.append((a, b))

    def quad(self, points):
        indices = [self.vertex(point) for point in points]
        for index in range(4):
            a, b = indices[index], indices[(index + 1) % 4]
            key = tuple(sorted((a, b)))
            if a != b and key not in self._edge_set:
                self._edge_set.add(key)
                self.edges.append((a, b))

    def mesh(self):
        if not self.vertices:
            return Mesh([(0.0, 0.0, 0.0)], [])
        return Mesh(self.vertices, self.edges)


def _make_wall_mesh(blueprint):
    builder = _MeshBuilder()
    size = blueprint.size
    for z in range(size):
        for x in range(size):
            if not blueprint.is_open((x, z)):
                continue
            x0, x1 = x * CELL_SIZE, (x + 1) * CELL_SIZE
            z0, z1 = z * CELL_SIZE, (z + 1) * CELL_SIZE
            sides = (
                ((-1, 0), ((x0, 0, z0), (x0, 0, z1),
                           (x0, WALL_HEIGHT, z1), (x0, WALL_HEIGHT, z0))),
                ((1, 0), ((x1, 0, z1), (x1, 0, z0),
                          (x1, WALL_HEIGHT, z0), (x1, WALL_HEIGHT, z1))),
                ((0, -1), ((x1, 0, z0), (x0, 0, z0),
                           (x0, WALL_HEIGHT, z0), (x1, WALL_HEIGHT, z0))),
                ((0, 1), ((x0, 0, z1), (x1, 0, z1),
                          (x1, WALL_HEIGHT, z1), (x0, WALL_HEIGHT, z1))),
            )
            for (dx, dz), points in sides:
                if not blueprint.is_open((x + dx, z + dz)):
                    builder.quad(points)
    return builder.mesh()


def _make_floor_mesh(blueprint):
    builder = _MeshBuilder()
    for z in range(blueprint.size):
        for x in range(blueprint.size):
            if blueprint.is_open((x, z)):
                x0, x1 = x * CELL_SIZE, (x + 1) * CELL_SIZE
                z0, z1 = z * CELL_SIZE, (z + 1) * CELL_SIZE
                builder.quad(((x0, 0.015, z0), (x1, 0.015, z0),
                              (x1, 0.015, z1), (x0, 0.015, z1)))
    return builder.mesh()


def _make_key_mesh(cell):
    cx, cz = cell_center(cell)
    y, radius = 1.05, KEY_RADIUS
    points = ((cx, y + radius, cz), (cx, y - radius, cz),
              (cx - radius, y, cz), (cx + radius, y, cz),
              (cx, y, cz - radius), (cx, y, cz + radius))
    edges = [(0, index) for index in range(2, 6)] + [
        (1, index) for index in range(2, 6)] + [(2, 4), (4, 3), (3, 5), (5, 2)]
    return Mesh(list(points), edges)


def _make_exit_mesh(cell):
    x, z = cell
    cx, cz = (x + 0.5) * CELL_SIZE, (z + 0.5) * CELL_SIZE
    half_width, height = 0.62, 2.05
    z_plane = cz
    points = [(cx - half_width, 0.04, z_plane),
              (cx + half_width, 0.04, z_plane),
              (cx + half_width, height, z_plane),
              (cx - half_width, height, z_plane),
              (cx, 0.04, z_plane - 0.05),
              (cx, height, z_plane - 0.05)]
    return Mesh(points, [(0, 1), (1, 2), (2, 3), (3, 0),
                         (4, 5), (0, 4), (1, 4), (2, 5), (3, 5)])


class MazeState:
    """Three-stage maze run with scoring, map discovery, and scan pulses."""
    def __init__(self, seed=7):
        self.seed = seed
        self.projection = "Perspective"
        self.look_drag = False
        self.level = 1
        self.total_score = 0
        self.best_score = self._load_best_score()
        self.restart(seed)

    def restart(self, seed=None, *, keep_run=False):
        if seed is not None:
            self.seed = seed
        if not keep_run:
            self.level = 1
            self.total_score = 0
        size = LEVEL_SIZES[min(self.level - 1, len(LEVEL_SIZES) - 1)]
        self.blueprint = MazeBlueprint.generate(size=size, seed=self.seed)
        self.player_x, self.player_z = self.blueprint.cell_center(self.blueprint.start)
        self.yaw = self._spawn_yaw()
        self.camera = MazeCamera((self.player_x, PLAYER_EYE_HEIGHT, self.player_z),
                                 self.yaw)
        self.keys_found = set()
        self.won = False
        self.paused = False
        self.campaign_complete = False
        self.elapsed = 0.0
        self.steps = 0
        self.scans_used = 0
        self.scan_flash = 0.0
        self.level_score = 0
        self.revealed_cells = set()
        self.message = "Find both signal keys, then reach the exit."
        self.message_time = 5.0
        self.wall_mesh = _make_wall_mesh(self.blueprint)
        self.floor_mesh = _make_floor_mesh(self.blueprint)
        self.key_meshes = {cell: _make_key_mesh(cell) for cell in self.blueprint.keys}
        self.exit_mesh = _make_exit_mesh(self.blueprint.exit)
        self.look_drag = False
        self._reveal_nearby()

    def new_maze(self):
        self.restart(self.seed + 1)

    def advance_level(self):
        if not self.won or self.level >= len(LEVEL_SIZES):
            return False
        self.level += 1
        self.restart(self.seed + 1, keep_run=True)
        self.message = f"Level {self.level}: find the signal keys."
        self.message_time = 4.0
        return True

    def toggle_pause(self):
        if self.won:
            return
        self.paused = not self.paused
        self.message = "Run paused. Press Esc or Resume when ready." if self.paused else "Run resumed."
        self.message_time = 2.5

    def scan(self):
        if self.paused or self.won or self.scans_used >= 3:
            return False
        self.scans_used += 1
        px, pz = self.player_cell
        for z in range(max(0, pz - 4), min(self.blueprint.size, pz + 5)):
            for x in range(max(0, px - 4), min(self.blueprint.size, px + 5)):
                if abs(x - px) + abs(z - pz) <= 4:
                    self.revealed_cells.add((x, z))
        self.scan_flash = 1.5
        left = 3 - self.scans_used
        self.message = f"Signal scan complete · {left} pulse{'s' if left != 1 else ''} left."
        self.message_time = 2.6
        return True

    @staticmethod
    def _record_path():
        local_app_data = os.environ.get('LOCALAPPDATA')
        root = Path(local_app_data) if local_app_data else Path.home() / '.local' / 'share'
        return root / 'RenderX' / 'maze_record.json'

    @classmethod
    def _load_best_score(cls):
        try:
            data = json.loads(cls._record_path().read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                return 0
            return max(0, int(data.get('best_score', 0)))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return 0

    def _save_best_score(self):
        try:
            path = self._record_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'best_score': self.best_score}), encoding='utf-8')
        except OSError:
            # A completed run remains playable if the machine disallows local saves.
            pass

    def toggle_projection(self):
        self.projection = ("Orthographic" if self.projection == "Perspective"
                           else "Perspective")

    def line_visible(self, camera_point):
        """Hide a maze line sample if a nearer wall blocks its view ray."""
        camera_x, camera_y, camera_z = camera_point
        sine, cosine = sin(self.yaw), cos(self.yaw)
        target_x = self.player_x + camera_x * cosine + camera_z * sine
        target_z = self.player_z - camera_x * sine + camera_z * cosine
        dx, dz = target_x - self.player_x, target_z - self.player_z
        if abs(dx) + abs(dz) < 1e-9:
            return True

        cell_x = int(self.player_x // CELL_SIZE)
        cell_z = int(self.player_z // CELL_SIZE)
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_z = 1 if dz > 0 else -1 if dz < 0 else 0
        infinity = float('inf')
        if step_x:
            boundary_x = ((cell_x + 1) * CELL_SIZE if step_x > 0
                          else cell_x * CELL_SIZE)
            max_x = (boundary_x - self.player_x) / dx
            delta_x = CELL_SIZE / abs(dx)
        else:
            max_x = delta_x = infinity
        if step_z:
            boundary_z = ((cell_z + 1) * CELL_SIZE if step_z > 0
                          else cell_z * CELL_SIZE)
            max_z = (boundary_z - self.player_z) / dz
            delta_z = CELL_SIZE / abs(dz)
        else:
            max_z = delta_z = infinity

        def wall_blocks(x, z, start_t, end_t):
            if self.blueprint.is_open((x, z)):
                return False
            start_height = PLAYER_EYE_HEIGHT + camera_y * start_t
            end_height = PLAYER_EYE_HEIGHT + camera_y * end_t
            return (max(start_height, end_height) >= 0 and
                    min(start_height, end_height) <= WALL_HEIGHT)

        previous_t = 0.0
        while min(max_x, max_z) < 1.0 - 1e-6:
            next_t = min(max_x, max_z)
            if abs(max_x - max_z) <= 1e-9:
                if (wall_blocks(cell_x + step_x, cell_z, previous_t, next_t) or
                        wall_blocks(cell_x, cell_z + step_z, previous_t, next_t)):
                    return False
                cell_x += step_x
                cell_z += step_z
                max_x += delta_x
                max_z += delta_z
            elif max_x < max_z:
                cell_x += step_x
                max_x += delta_x
            else:
                cell_z += step_z
                max_z += delta_z
            if wall_blocks(cell_x, cell_z, previous_t, next_t):
                return False
            previous_t = next_t
        return True

    def visibility_for(self, viewport, focal_length):
        """Build one reusable wall-depth lookup for the active maze frame."""
        if self.projection == 'Perspective':
            return _PerspectiveWallVisibility(self, viewport, focal_length)
        return self.line_visible

    def _spawn_yaw(self):
        x, z = self.blueprint.start
        for dx, dz, yaw in ((0, 1, 0.0), (1, 0, pi / 2),
                            (0, -1, pi), (-1, 0, -pi / 2)):
            if self.blueprint.is_open((x + dx, z + dz)):
                return yaw % tau
        return 0.0

    @property
    def key_count(self):
        return len(self.blueprint.keys)

    @property
    def exit_unlocked(self):
        return len(self.keys_found) == self.key_count

    @property
    def player_cell(self):
        return (int(self.player_x // CELL_SIZE), int(self.player_z // CELL_SIZE))

    def turn(self, amount):
        if not self.won and not self.paused:
            self.yaw = (self.yaw + amount) % tau
            self.camera.yaw = self.yaw

    def step(self, direction):
        if self.won or self.paused:
            return
        distance = direction * 0.58
        self._move_by(sin(self.yaw) * distance, cos(self.yaw) * distance)

    def update(self, keys, dt):
        """Apply held-key movement; callers update only while Maze is open."""
        if self.won or self.paused:
            return
        dt = min(max(float(dt), 0.0), config.MAX_DT)
        self.elapsed += dt
        self.message_time = max(0.0, self.message_time - dt)
        self.scan_flash = max(0.0, self.scan_flash - dt)
        turn = ((any(keys[key] for key in MAZE_KEYS["turn_right"])) -
                (any(keys[key] for key in MAZE_KEYS["turn_left"])))
        self.turn(turn * TURN_SPEED * dt)

        forward = ((any(keys[key] for key in MAZE_KEYS["move_forward"])) -
                   (any(keys[key] for key in MAZE_KEYS["move_backward"])))
        strafe = (keys[MAZE_KEYS["strafe_right"]] -
                  keys[MAZE_KEYS["strafe_left"]])
        if forward or strafe:
            length = sqrt(forward * forward + strafe * strafe)
            forward, strafe = forward / length, strafe / length
            sine, cosine = sin(self.yaw), cos(self.yaw)
            distance = MOVE_SPEED * dt
            dx = (sine * forward + cosine * strafe) * distance
            dz = (cosine * forward - sine * strafe) * distance
            self._move_by(dx, dz)

    def handle_mouse(self, events, viewport=(32, 100, 820, 640)):
        """Left-drag in the 3D viewport turns the player horizontally."""
        viewport = pygame.Rect(viewport)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTONS["primary"]:
                self.look_drag = viewport.collidepoint(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_BUTTONS["primary"]:
                self.look_drag = False
            elif event.type in (pygame.WINDOWLEAVE, pygame.WINDOWFOCUSLOST,
                                pygame.WINDOWMINIMIZED):
                self.look_drag = False
            elif event.type == pygame.MOUSEMOTION and self.look_drag:
                if viewport.collidepoint(event.pos):
                    self.turn(event.rel[0] * config.DRAG_ROTATION)
                else:
                    self.look_drag = False

    def apply_action(self, action):
        if action == "turn-left":
            self.turn(-pi / 12)
        elif action == "turn-right":
            self.turn(pi / 12)
        elif action == "forward":
            self.step(1)
        elif action == "backward":
            self.step(-1)
        elif action == "new-maze":
            self.new_maze()
        elif action == "projection":
            self.toggle_projection()
        elif action == "pause":
            self.toggle_pause()
        elif action == "scan":
            self.scan()
        elif action == "continue":
            self.advance_level()

    def _is_blocked(self, x, z):
        if x < 0 or z < 0 or x >= self.blueprint.size * CELL_SIZE or z >= self.blueprint.size * CELL_SIZE:
            return True
        min_x = max(0, int((x - PLAYER_RADIUS) // CELL_SIZE))
        max_x = min(self.blueprint.size - 1, int((x + PLAYER_RADIUS) // CELL_SIZE))
        min_z = max(0, int((z - PLAYER_RADIUS) // CELL_SIZE))
        max_z = min(self.blueprint.size - 1, int((z + PLAYER_RADIUS) // CELL_SIZE))
        for cell_z in range(min_z, max_z + 1):
            for cell_x in range(min_x, max_x + 1):
                if self.blueprint.cells[cell_z][cell_x] == 0:
                    continue
                left, right = cell_x * CELL_SIZE, (cell_x + 1) * CELL_SIZE
                top, bottom = cell_z * CELL_SIZE, (cell_z + 1) * CELL_SIZE
                nearest_x = min(max(x, left), right)
                nearest_z = min(max(z, top), bottom)
                if hypot(x - nearest_x, z - nearest_z) < PLAYER_RADIUS:
                    return True
        return False

    def _move_by(self, dx, dz):
        old_cell = self.player_cell
        next_x = self.player_x + dx
        if not self._is_blocked(next_x, self.player_z):
            self.player_x = next_x
        next_z = self.player_z + dz
        if not self._is_blocked(self.player_x, next_z):
            self.player_z = next_z
        self.camera.position = (self.player_x, PLAYER_EYE_HEIGHT, self.player_z)
        new_cell = self.player_cell
        self.steps += abs(new_cell[0] - old_cell[0]) + abs(new_cell[1] - old_cell[1])
        if new_cell != old_cell:
            self._reveal_nearby()
        self._collect_or_finish()

    def _reveal_nearby(self):
        px, pz = self.player_cell
        for z in range(max(0, pz - 2), min(self.blueprint.size, pz + 3)):
            for x in range(max(0, px - 2), min(self.blueprint.size, px + 3)):
                self.revealed_cells.add((x, z))

    def _collect_or_finish(self):
        for index, cell in enumerate(self.blueprint.keys):
            if index in self.keys_found:
                continue
            key_x, key_z = self.blueprint.cell_center(cell)
            if hypot(self.player_x - key_x, self.player_z - key_z) <= 0.62:
                self.keys_found.add(index)
                remaining = self.key_count - len(self.keys_found)
                self.message = ("Signal key recovered. Keep exploring." if remaining else
                                "All keys recovered. The exit is open!")
                self.message_time = 3.0

        exit_x, exit_z = self.blueprint.cell_center(self.blueprint.exit)
        if hypot(self.player_x - exit_x, self.player_z - exit_z) <= 0.62:
            if self.exit_unlocked:
                self.won = True
                self.level_score = max(100, 1500 - int(self.elapsed * 4) -
                                       self.steps * 5 - self.scans_used * 60)
                self.total_score += self.level_score
                self.campaign_complete = self.level >= len(LEVEL_SIZES)
                if self.campaign_complete and self.total_score > self.best_score:
                    self.best_score = self.total_score
                    self._save_best_score()
                self.message = ("Campaign complete. You found every signal." if
                                self.campaign_complete else
                                f"Level {self.level} cleared. The next maze is ready.")
                self.message_time = 60.0
            else:
                self.message = "The exit is locked. Find both signal keys."
                self.message_time = 2.5


def cell_path(blueprint, start, goal):
    """Return the shortest floor-cell path, useful for navigation and tests."""
    parents = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        x, z = cell
        for dx, dz in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            neighbor = (x + dx, z + dz)
            if blueprint.is_open(neighbor) and neighbor not in parents:
                parents[neighbor] = cell
                queue.append(neighbor)
    path, cell = [], goal
    while cell is not None:
        path.append(cell)
        cell = parents[cell]
    return tuple(reversed(path))
