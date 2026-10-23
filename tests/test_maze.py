"""Procedural maze generation, first-person movement, and dashboard wiring."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

from math import hypot, pi
import unittest

import pygame

from renderx.camera import Camera
from renderx.dashboard import Dashboard, SIZE
from renderx.input import Controls
from renderx.maze import (MazeBlueprint, MazeCamera, MazeState, cell_path)
from renderx.maze_ui import draw_maze_sidebar, draw_maze_view
from renderx.models import make_library
from renderx.scene import Scene
from renderx.ui import Panel


class MazeGenerationTests(unittest.TestCase):
    def test_seed_repeats_the_same_connected_maze_and_objectives(self):
        first = MazeBlueprint.generate(seed=42)
        second = MazeBlueprint.generate(seed=42)
        self.assertEqual(first, second)
        self.assertNotEqual(first.cells, MazeBlueprint.generate(seed=43).cells)
        objectives = (first.start, *first.keys, first.exit)
        self.assertEqual(len(set(objectives)), len(objectives))
        for objective in objectives:
            self.assertTrue(first.is_open(objective))
        for goal in objectives[1:]:
            path = cell_path(first, first.start, goal)
            self.assertEqual(path[0], first.start)
            self.assertEqual(path[-1], goal)
            self.assertTrue(all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
                                for a, b in zip(path, path[1:])))

    def test_maze_size_rejects_even_or_too_small_values(self):
        for size in (0, 6, 8, 10):
            with self.assertRaises(ValueError):
                MazeBlueprint.generate(size=size)


class MazeMovementTests(unittest.TestCase):
    def test_camera_yaw_maps_the_forward_direction_to_camera_depth(self):
        camera = MazeCamera((0, 0, 0), 0)
        self.assertEqual(camera.relative_point((0, 0, 3)), (0, 0, 3))
        camera.yaw = pi / 2
        x, y, z = camera.relative_point((3, 0, 0))
        self.assertAlmostEqual(x, 0)
        self.assertEqual(y, 0)
        self.assertEqual(z, 3)

    def test_grid_visibility_keeps_open_corridor_and_hides_lines_behind_walls(self):
        state = MazeState(seed=9)
        x, z = state.blueprint.start
        open_cell = next((x + dx, z + dz)
                         for dx, dz in ((0, 1), (1, 0), (0, -1), (-1, 0))
                         if state.blueprint.is_open((x + dx, z + dz)))
        wall_cell = next((x + dx, z + dz)
                         for dx, dz in ((0, 1), (1, 0), (0, -1), (-1, 0))
                         if not state.blueprint.is_open((x + dx, z + dz)))
        open_x, open_z = state.blueprint.cell_center(open_cell)
        wall_x, wall_z = state.blueprint.cell_center(wall_cell)
        self.assertTrue(state.line_visible(
            state.camera.relative_point((open_x, 1.05, open_z))))
        self.assertFalse(state.line_visible(
            state.camera.relative_point((wall_x, 1.05, wall_z))))

    def test_walk_turn_and_wall_collision(self):
        state = MazeState(seed=9)
        initial = (state.player_x, state.player_z)
        state.step(1)
        self.assertGreater(hypot(state.player_x - initial[0],
                                 state.player_z - initial[1]), 0.1)
        old_yaw = state.yaw
        state.turn(pi / 4)
        self.assertNotEqual(state.yaw, old_yaw)
        self.assertEqual(state.camera.yaw, state.yaw)

        x, z = state.blueprint.start
        for dx, dz, yaw in ((0, 1, 0), (1, 0, pi / 2),
                            (0, -1, pi), (-1, 0, -pi / 2)):
            if not state.blueprint.is_open((x + dx, z + dz)):
                state.player_x, state.player_z = state.blueprint.cell_center((x, z))
                state.yaw = yaw % (2 * pi)
                state.camera.yaw = state.yaw
                before = (state.player_x, state.player_z)
                for _ in range(8):
                    state.step(1)
                self.assertLess(hypot(state.player_x - before[0],
                                      state.player_z - before[1]), 0.8)
                break
        else:
            self.fail('The maze start must have at least one blocked side.')

    def test_keys_unlock_the_exit_and_the_player_can_finish(self):
        state = MazeState(seed=12)
        route = (state.blueprint.start, *state.blueprint.keys,
                 state.blueprint.exit)
        current = state.blueprint.start
        for goal in route[1:]:
            for cell in cell_path(state.blueprint, current, goal)[1:]:
                target_x, target_z = state.blueprint.cell_center(cell)
                state._move_by(target_x - state.player_x,
                               target_z - state.player_z)
            current = goal
            if current in state.blueprint.keys:
                self.assertGreaterEqual(len(state.keys_found), 1)
        self.assertTrue(state.exit_unlocked)
        self.assertTrue(state.won)
        self.assertIn('cleared', state.message.lower())

    def test_new_maze_advances_seed_and_resets_progress(self):
        state = MazeState(seed=20)
        state.keys_found.add(0)
        state.new_maze()
        self.assertEqual(state.seed, 21)
        self.assertFalse(state.keys_found)
        self.assertFalse(state.won)

    def test_live_projection_toggle_is_preserved_for_the_next_maze(self):
        state = MazeState(seed=20)
        state.toggle_projection()
        self.assertEqual(state.projection, 'Orthographic')
        state.new_maze()
        self.assertEqual(state.projection, 'Orthographic')
        state.apply_action('projection')
        self.assertEqual(state.projection, 'Perspective')


class MazeDrawingTests(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        self.target = pygame.Surface(SIZE)
        self.small = pygame.font.Font(None, 20)
        self.heading = pygame.font.Font(None, 28)
        self.body = pygame.font.Font(None, 25)

    def tearDown(self):
        pygame.quit()

    def test_maze_scene_and_live_map_draw_without_leaking_clips(self):
        state = MazeState()
        original_clip = self.target.get_clip()
        draw_maze_view(self.target, state, pygame.Rect(32, 100, 820, 640),
                       self.heading, self.small)
        draw_maze_sidebar(self.target, state, pygame.Rect(880, 100, 448, 640),
                          self.heading, self.body, self.small)
        self.assertEqual(self.target.get_clip(), original_clip)

    def test_maze_buttons_turn_move_and_generate_another_map(self):
        ui = Dashboard(Panel())
        ui.active_destination = 'Maze'
        state = MazeState(seed=5)
        scene, models, controls = Scene(), make_library(), Controls()

        def click(action):
            ui.layout(scene, models, maze_state=state)
            event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                       pos=ui.buttons[action].center)
            ui.events([event], scene, models, None, controls, state)

        yaw = state.yaw
        click(('maze_action', 'turn-left'))
        self.assertNotEqual(state.yaw, yaw)
        position = (state.player_x, state.player_z)
        click(('maze_action', 'forward'))
        self.assertGreater(hypot(state.player_x - position[0],
                                 state.player_z - position[1]), 0.1)
        click(('maze_action', 'new-maze'))
        self.assertEqual(state.seed, 6)
        ui.events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)],
                  scene, models, None, controls, state)
        self.assertEqual(state.projection, 'Orthographic')


if __name__ == '__main__':
    unittest.main()
