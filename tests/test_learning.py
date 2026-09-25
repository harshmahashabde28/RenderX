"""Known coordinate answers plus real headless learning-mode interactions."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from collections import defaultdict
from math import pi
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pygame
from renderx import config
from renderx.app import run
from renderx.camera import Camera
from renderx.input import Controls
from renderx.learning import LearningState, STAGE_COUNT
from renderx.models import make_cube
from renderx.pipeline import snapshot_vertex
from renderx.renderer import draw_selected_vertex, VIEWPORT
from renderx.scene import Scene
from renderx.screenshots import save_screenshot
from renderx.transform import transform_vertex
from renderx.ui import Panel


def key(value):
    return pygame.event.Event(pygame.KEYDOWN, key=value)


class PipelineTests(unittest.TestCase):
    def assert_point(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for value, target in zip(actual, expected):
            self.assertAlmostEqual(value, target, places=7)

    def test_every_stage_with_known_values(self):
        scene = Scene(angles=(pi/2, pi/2, pi/2), position=(1, 2, 10), scale=2)
        stages = snapshot_vertex((1, 2, 3), scene, Camera((1, 2, 3)))
        expected = [(1, 2, 3), (2, 4, 6), (2, -6, 4), (4, -6, -2),
                    (6, 4, -2), (7, 6, 8), (6, 4, 5), (950, 10)]
        self.assertEqual(len(stages), STAGE_COUNT)
        for stage, point in zip(stages, expected):
            with self.subTest(stage=stage.name):
                self.assert_point(stage.coordinates, point)
                self.assertTrue(stage.formula)
                self.assertTrue(stage.explanation)

    def test_individual_scale_and_translation(self):
        scene = Scene(angles=(0, 0, 0), position=(3, -4, 10), scale=.5)
        stages = snapshot_vertex((2, 4, -6), scene, Camera())
        self.assert_point(stages[1].coordinates, (1, 2, -3))
        self.assert_point(stages[5].coordinates, (4, -2, 7))

    def test_renderer_and_snapshot_agree_across_poses(self):
        mesh = make_cube()
        for angles in [(0, 0, 0), (.2, -.5, 1.3), (pi, pi/2, pi/4)]:
            for mode in ("Perspective", "Orthographic"):
                scene = Scene(angles=angles, position=(.3, -.7, 2),
                              scale=1.2, projection=mode)
                camera = Camera((.1, .2, .3))
                for point in mesh.vertices:
                    stages = snapshot_vertex(point, scene, camera)
                    world = transform_vertex(point, scene)
                    self.assertEqual(stages[5].coordinates, world)
                    self.assertEqual(stages[-1].coordinates, camera.project(world, mode))

    def test_snapshots_do_not_mutate_or_follow_later_state(self):
        mesh = make_cube()
        original = mesh.vertices.copy()
        scene = Scene()
        before = snapshot_vertex(mesh.vertices[0], scene, Camera())
        saved_world = before[5].coordinates
        for _ in range(100):
            scene.rotate(.1, .2, .3)
            snapshot_vertex(mesh.vertices[0], scene, Camera())
        self.assertEqual(mesh.vertices, original)
        self.assertEqual(before[5].coordinates, saved_world)
        self.assertEqual(before[0].coordinates, original[0])

    def test_projection_modes_and_depth(self):
        for mode in ("Perspective", "Orthographic"):
            scene = Scene(angles=(0, 0, 0), projection=mode)
            near = snapshot_vertex((1, 1, 0), scene, Camera())[-1]
            scene.position = (0, 0, 10)
            far = snapshot_vertex((1, 1, 0), scene, Camera())[-1]
            self.assert_point(near.coordinates, (500, 280))
            self.assert_point(far.coordinates, (455, 325) if mode == "Perspective"
                              else (500, 280))
            self.assertIn("x/z" if mode == "Perspective" else "k*x", near.formula[0])

    def test_hidden_boundary_and_nonfinite_vertices(self):
        for mode in ("Perspective", "Orthographic"):
            scene = Scene(angles=(0, 0, 0), position=(0, 0, 0), projection=mode)
            for point in [(0, 0, 0), (0, 0, -.1), (float('nan'), 0, 1)]:
                stage = snapshot_vertex(point, scene, Camera())[-1]
                self.assertIsNone(stage.coordinates)
                self.assertIn("Connected edges", stage.explanation)
            self.assert_point(snapshot_vertex((0, 0, .1), scene, Camera())[-1].coordinates,
                              config.CENTRE)


class LearningStateTests(unittest.TestCase):
    def test_vertex_and_stage_wraparound(self):
        state = LearningState()
        state.select_vertex(-1, 8)
        self.assertEqual(state.selected_vertex, 7)
        state.select_vertex(1, 8)
        self.assertEqual(state.selected_vertex, 0)
        state.select_vertex(15, 8)
        self.assertEqual(state.selected_vertex, 7)
        state.select_vertex(0, 5)
        self.assertEqual(state.selected_vertex, 2)
        state.select_vertex(1, 0)
        self.assertEqual(state.selected_vertex, 0)
        state.select_stage(-1)
        self.assertEqual(state.stage_index, 7)
        state.select_stage(1)
        self.assertEqual(state.stage_index, 0)

    def test_modes_keep_selection_and_stage(self):
        state = LearningState(selected_vertex=3, stage_index=5)
        for expected in ("Pipeline", "Compare", "Mesh", "Lesson", "Challenge", "Demo", "Explore"):
            state.cycle_mode()
            self.assertEqual(state.mode, expected)
            self.assertEqual((state.selected_vertex, state.stage_index), (3, 5))


class LearningInteractionTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        self.panel = Panel()

    def tearDown(self):
        pygame.quit()

    def test_learning_keys_preserve_pose_and_cancel_drag(self):
        scene = Scene(angles=(1, 2, 3), position=(.5, -.2, 7), scale=.8)
        before = (scene.angles, scene.position, scene.scale)
        controls, learning = Controls(), LearningState()
        controls.drag = "xy"
        events = [key(pygame.K_TAB), key(pygame.K_PERIOD), key(pygame.K_RIGHTBRACKET)]
        controls.update(scene, events, defaultdict(int, {pygame.K_w: 1}),
                        .04, self.panel, (200, 200), learning=learning)
        self.assertEqual(learning.mode, "Pipeline")
        self.assertEqual(learning.stage_index, 1)
        self.assertEqual(controls.vertex_step, 1)
        self.assertIsNone(controls.drag)
        self.assertEqual((scene.angles, scene.position, scene.scale), before)

    def test_focus_loss_blocks_learning_keys(self):
        controls, learning = Controls(), LearningState()
        controls.update(Scene(), [pygame.event.Event(pygame.WINDOWFOCUSLOST),
                                 key(pygame.K_TAB), key(pygame.K_PERIOD),
                                 key(pygame.K_RIGHTBRACKET)],
                        defaultdict(int), 0, self.panel, (0, 0), learning=learning)
        self.assertEqual(learning, LearningState())
        self.assertEqual(controls.vertex_step, 0)

    def test_highlight_visible_hidden_and_outside_viewport(self):
        screen = pygame.Surface((config.WIDTH, config.HEIGHT))
        screen.fill((0, 0, 0))
        self.assertTrue(draw_selected_vertex(screen, config.CENTRE, 3, self.panel.small))
        self.assertEqual(screen.get_at(config.CENTRE)[:3], config.SELECTED)
        for point in (None, (-100, 300), (config.VIEW_WIDTH + 2, 300)):
            self.assertFalse(draw_selected_vertex(screen, point, 3, self.panel.small))
        self.assertEqual(screen.get_clip(), screen.get_rect())
        self.assertEqual(screen.get_at((VIEWPORT.right + 2, 300))[:3], (0, 0, 0))

    def test_app_learning_shape_obj_reset_export_and_exit(self):
        frames = [[],
                  [key(pygame.K_TAB), key(pygame.K_COMMA), key(pygame.K_LEFTBRACKET)],
                  [key(pygame.K_p), key(pygame.K_x)],
                  [key(pygame.K_2), key(pygame.K_PERIOD)],
                  [key(pygame.K_o), key(pygame.K_COMMA)],
                  [key(pygame.K_r), key(pygame.K_F12)],
                  [key(pygame.K_TAB)], [key(pygame.K_F1)], [key(pygame.K_TAB)],
                  [key(pygame.K_ESCAPE)]]
        observed = []
        original_draw = Panel.draw

        def record(panel, surface, scene, mesh, fps, learning, snapshots):
            observed.append((learning.mode, learning.selected_vertex,
                             learning.stage_index, scene.shape, scene.projection,
                             scene.axes_visible, surface.get_size()))
            original_draw(panel, surface, scene, mesh, fps, learning, snapshots)

        with tempfile.TemporaryDirectory() as folder:
            with patch('pygame.event.get', side_effect=frames), \
                 patch('pygame.key.get_pressed', return_value=defaultdict(int)), \
                 patch.object(Panel, 'draw', record), \
                 patch('renderx.app.save_screenshot',
                       side_effect=lambda surface: save_screenshot(surface, folder)):
                with patch('renderx.app.initial_size', return_value=(1360, 900)):
                    run()
            captures = list(Path(folder).glob('*.png'))
            self.assertEqual(len(captures), 1)
            self.assertEqual(pygame.image.load(str(captures[0])).get_size(), (1360, 900))
        self.assertEqual(observed[0][:4], ('Explore', 0, 0, 'Cube'))
        self.assertEqual(observed[1][:4], ('Pipeline', 7, 7, 'Cube'))
        self.assertEqual(observed[2][4:6], ('Orthographic', False))
        self.assertEqual(observed[3][:4], ('Pipeline', 1, 7, 'Pyramid'))
        self.assertEqual(observed[4][:4], ('Pipeline', 9, 7, 'OBJ house'))
        self.assertEqual(observed[5], observed[4])
        self.assertEqual(observed[6][0], 'Compare')
        self.assertEqual(observed[6][-1], (1120, 740))
        self.assertEqual(observed[7][0], 'Explore')
        self.assertEqual(observed[7][-1], (1120, 740))
        self.assertEqual(observed[8], observed[5])
        self.assertFalse(pygame.display.get_init())
