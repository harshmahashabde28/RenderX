"""Projection comparisons with known answers and real headless drawing/input."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pygame
from renderx import config
from renderx.app import run
from renderx.axes import draw_axes
from renderx.camera import Camera
from renderx.comparison import (COMPARE_FOCAL_LENGTH, VIEWS, draw_comparison,
                                projected_bounds)
from renderx.input import Controls
from renderx.learning import LearningState
from renderx.mesh import Mesh
from renderx.models import make_cube
from renderx.renderer import draw_wireframe
from renderx.scene import Scene
from renderx.screenshots import save_screenshot
from renderx.transform import transform_vertex
from renderx.ui import Panel


def key(value):
    return pygame.event.Event(pygame.KEYDOWN, key=value)


class ComparisonMathTests(unittest.TestCase):
    def test_custom_centres_focal_length_and_shared_camera(self):
        camera = Camera((1, 2, 3))
        self.assertEqual(camera.project((2, 4, 13), centre=(100, 200), focal_length=300),
                         (130, 140))
        self.assertEqual(camera.project((2, 4, 13), 'Orthographic',
                                       centre=(100, 200), focal_length=300), (160, 80))
        self.assertEqual(camera.project((2, 4, 13), centre=(500, 200), focal_length=300),
                         (530, 140))
        self.assertEqual(camera.position, (1, 2, 3))

    def test_custom_view_edge_uses_near_plane_intersection(self):
        camera = Camera()
        for mode, expected in [('Perspective', (3400, -6400)),
                               ('Orthographic', (166, 68))]:
            segment = camera.project_edge((0, 0, -1), (2, 4, 1), mode,
                                          centre=(100, 200), focal_length=300)
            for actual, value in zip(segment[0], expected):
                self.assertAlmostEqual(actual, value)
            self.assertIsNone(camera.project_edge((0, 0, -2), (2, 4, -1), mode,
                                                  centre=(100, 200), focal_length=300))

    def test_depth_halves_perspective_plane_size_only(self):
        mesh = Mesh([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)],
                    [(0, 1), (1, 2), (2, 3), (3, 0)])
        sizes = {}
        for mode, viewport in VIEWS:
            for depth in (5, 10):
                scene = Scene(angles=(0, 0, 0), position=(0, 0, depth))
                points = [transform_vertex(point, scene) for point in mesh.vertices]
                bounds = projected_bounds(points, mesh.edges, Camera(), mode, viewport.center)
                sizes[mode, depth] = (bounds[2] - bounds[0], bounds[3] - bounds[1])
        self.assertEqual(sizes['Perspective', 5], (120, 120))
        self.assertEqual(sizes['Perspective', 10], (60, 60))
        self.assertEqual(sizes['Orthographic', 5], (120, 120))
        self.assertEqual(sizes['Orthographic', 10], (120, 120))

    def test_bounds_include_crossing_edges_but_omit_hidden_edges(self):
        points = [(0, 0, -1), (2, 4, 1), (0, 0, -2)]
        for mode, viewport in VIEWS:
            self.assertIsNotNone(projected_bounds(points, [(0, 1)], Camera(), mode,
                                                  viewport.center))
            self.assertIsNone(projected_bounds(points, [(0, 2)], Camera(), mode,
                                               viewport.center))


class ComparisonInteractionTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        self.surface = pygame.Surface((config.WIDTH, config.HEIGHT))
        self.panel = Panel()

    def tearDown(self):
        pygame.quit()

    def test_rendered_panes_share_vertex_camera_and_pose(self):
        mesh = make_cube()
        scene = Scene(angles=(.2, .3, .4), position=(.2, -.1, 6), scale=.8)
        camera = Camera((.1, -.2, .3))
        learning = LearningState(mode='Compare', selected_vertex=2)
        original = deepcopy((mesh, scene, camera, learning))
        self.surface.fill((255, 0, 0))
        draw_comparison(self.surface, mesh, scene, camera, learning, self.panel.small)
        selected = transform_vertex(mesh.vertices[2], scene)
        for mode, viewport in VIEWS:
            point = camera.project(selected, mode, centre=viewport.center,
                                   focal_length=COMPARE_FOCAL_LENGTH)
            pixel = tuple(round(value) for value in point)
            self.assertTrue(viewport.collidepoint(pixel))
            self.assertEqual(self.surface.get_at(pixel)[:3], config.SELECTED)
        self.assertEqual((mesh, scene, camera, learning), original)
        self.assertEqual(self.surface.get_clip(), self.surface.get_rect())
        self.assertEqual(self.surface.get_at((config.VIEW_WIDTH + 2, 300))[:3], (255, 0, 0))

    def test_subviewport_and_existing_clip_are_respected(self):
        self.surface.fill((255, 0, 0))
        viewport = VIEWS[1][1]
        caller_clip = pygame.Rect(viewport.left, viewport.top, 180, viewport.height)
        self.surface.set_clip(caller_clip)
        drawn = draw_wireframe(self.surface, make_cube(), Scene(), Camera(),
                               viewport=viewport, projection='Orthographic',
                               focal_length=COMPARE_FOCAL_LENGTH)
        self.assertEqual(drawn, 12)
        draw_axes(self.surface, Camera(), 'Orthographic', self.panel.small,
                  viewport=viewport, focal_length=COMPARE_FOCAL_LENGTH)
        self.assertEqual(self.surface.get_clip(), caller_clip)
        self.assertEqual(self.surface.get_at((viewport.right - 2, 300))[:3], (255, 0, 0))
        self.assertEqual(self.surface.get_at(VIEWS[0][1].center)[:3], (255, 0, 0))
        self.assertNotEqual(self.surface.get_at((viewport.left + 3, 300))[:3], (255, 0, 0))

    def test_projection_toggle_and_mode_cycle_preserve_pose(self):
        scene = Scene(angles=(.2, .3, .4), position=(.4, -.2, 7), scale=.7)
        pose = (scene.angles, scene.position, scene.scale, scene.shape)
        learning = LearningState(mode='Compare', selected_vertex=3, stage_index=5)
        controls = Controls()
        for expected in ('Orthographic', 'Perspective'):
            controls.update(scene, [key(pygame.K_p)], defaultdict(int), 0,
                            self.panel, (200, 300), learning=learning)
            self.assertEqual(scene.projection, expected)
            self.assertEqual((scene.angles, scene.position, scene.scale, scene.shape), pose)
            draw_comparison(self.surface, make_cube(), scene, Camera(), learning, self.panel.small)
        for mode in ('Mesh', 'Lesson', 'Challenge', 'Demo', 'Explore', 'Pipeline', 'Compare'):
            controls.update(scene, [key(pygame.K_TAB)], defaultdict(int), 0,
                            self.panel, (200, 300), learning=learning)
            self.assertEqual(learning.mode, mode)
            self.assertEqual((learning.selected_vertex, learning.stage_index), (3, 5))
            self.assertEqual((scene.angles, scene.position, scene.scale, scene.shape), pose)

    def test_guide_toggle_is_optional_and_focus_safe(self):
        scene, controls = Scene(), Controls()
        learning = LearningState(mode='Compare')
        controls.update(scene, [key(pygame.K_v)], defaultdict(int), 0,
                        self.panel, (200, 300), learning=learning)
        self.assertFalse(learning.guides_visible)
        draw_comparison(self.surface, make_cube(), scene, Camera(), learning, self.panel.small)
        controls.update(scene, [pygame.event.Event(pygame.WINDOWFOCUSLOST), key(pygame.K_v)],
                        defaultdict(int), 0, self.panel, (200, 300), learning=learning)
        self.assertFalse(learning.guides_visible)
        self.assertEqual(scene, Scene())

    def test_comparison_camera_crossing_no_bleed(self):
        mesh = make_cube()
        for depth in (5, 1, .1, 0, -1, -3):
            self.surface.fill((255, 0, 0))
            draw_comparison(self.surface, mesh, Scene(position=(0, 0, depth)), Camera(),
                            LearningState(mode='Compare'), self.panel.small)
            # The gutter and panel stay clear even for large near-plane projections.
            self.assertEqual(self.surface.get_at((410, 410))[:3], config.BACKGROUND)
            self.assertEqual(self.surface.get_at((822, 410))[:3], (255, 0, 0))

    def test_mouse_pan_in_either_pane_updates_the_single_scene(self):
        for _, viewport in VIEWS:
            scene, controls = Scene(), Controls()
            x, y = viewport.center
            events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2, pos=(x, y)),
                      pygame.event.Event(pygame.MOUSEMOTION, pos=(x+20, y-20), rel=(20, -20))]
            controls.update(scene, events, defaultdict(int), 0, self.panel, (x+20, y-20),
                            learning=LearningState(mode='Compare'))
            self.assertEqual(scene.position, (.1, .1, 5))

    def test_app_compare_depth_switches_export_reset_and_exit(self):
        frames = [[key(pygame.K_TAB), key(pygame.K_TAB)], [],
                  [key(pygame.K_p), key(pygame.K_x), key(pygame.K_v), key(pygame.K_PERIOD)],
                  [key(pygame.K_F12)], [key(pygame.K_2)], [key(pygame.K_o)],
                  [key(pygame.K_r)], [key(pygame.K_F1)], [key(pygame.K_TAB)],
                  [pygame.event.Event(pygame.QUIT)]]
        held = [defaultdict(int) for _ in frames]
        held[1][pygame.K_PAGEDOWN] = 1
        observed = []
        draw = Panel.draw

        def record(panel, surface, scene, mesh, fps, learning, snapshots):
            observed.append((learning.mode, scene.shape, scene.position,
                             scene.projection, scene.axes_visible,
                             learning.selected_vertex, learning.guides_visible))
            draw(panel, surface, scene, mesh, fps, learning, snapshots)

        with tempfile.TemporaryDirectory() as directory:
            with patch('pygame.event.get', side_effect=frames), \
                 patch('pygame.key.get_pressed', side_effect=held), \
                 patch('pygame.time.Clock') as clock, \
                 patch.object(Panel, 'draw', record), \
                 patch('renderx.app.save_screenshot',
                       side_effect=lambda screen: save_screenshot(screen, directory)):
                clock.return_value.tick.return_value = 40
                clock.return_value.get_fps.return_value = 25
                run()
            images = list(Path(directory).glob('*.png'))
            self.assertEqual(len(images), 1)
            self.assertEqual(pygame.image.load(str(images[0])).get_size(), (1360, 900))
        self.assertEqual(observed[0], ('Compare', 'Cube', (0, 0, 5), 'Perspective', True, 0, True))
        self.assertAlmostEqual(observed[1][2][2], 5.04)
        self.assertEqual(observed[2][2], observed[1][2])
        self.assertEqual(observed[2][3:], ('Orthographic', False, 1, False))
        self.assertEqual(observed[3], observed[2])
        self.assertEqual(observed[4][1:3], ('Pyramid', (0, 0, 5)))
        self.assertEqual(observed[5][1:3], ('OBJ house', (0, 0, 5)))
        self.assertEqual(observed[6], observed[5])
        self.assertEqual(observed[7][0], 'Explore')
        self.assertEqual(observed[8][0], 'Pipeline')
        self.assertEqual(observed[8][3:], ('Orthographic', False, 0, False))
        self.assertFalse(pygame.display.get_init())
