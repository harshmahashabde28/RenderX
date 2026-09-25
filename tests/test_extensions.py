"""Regression checks for the next development phase."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
from collections import defaultdict
import unittest
import pygame
from renderx.camera import Camera, project_orthographic
from renderx.scene import Scene
from renderx.input import Controls
from renderx.ui import Panel


class ProjectionTests(unittest.TestCase):
    def test_orthographic_ignores_depth_and_camera_is_shared(self):
        self.assertEqual(project_orthographic((1, 2, 5)),
                         project_orthographic((1, 2, 10)))
        self.assertEqual(Camera((1, 2, 3)).project((2, 4, 8), "Orthographic"),
                         project_orthographic((1, 2, 5)))
        self.assertIsNone(project_orthographic((1, 2, -1)))

    def test_toggle_preserves_pose_and_toggles_back(self):
        pygame.font.init()
        try:
            scene = Scene(angles=(1, 2, 3), position=(.5, -.5, 7), scale=.7)
            before = (scene.angles, scene.position, scene.scale, scene.shape)
            controls, panel = Controls(), Panel()
            for expected in ["Orthographic", "Perspective"]:
                controls.update(scene, [pygame.event.Event(pygame.KEYDOWN,
                                key=pygame.K_p)], defaultdict(int), 0, panel, (0, 0))
                self.assertEqual(scene.projection, expected)
                self.assertEqual((scene.angles, scene.position, scene.scale,
                                  scene.shape), before)
        finally:
            pygame.font.quit()


class AxesTests(unittest.TestCase):
    def test_draw_both_modes_and_hidden_endpoints(self):
        from renderx.axes import draw_axes
        from renderx import config
        pygame.font.init()
        try:
            surface = pygame.Surface((config.WIDTH, config.HEIGHT))
            font = pygame.font.Font(None, 21)
            for mode in ["Perspective", "Orthographic"]:
                self.assertEqual(draw_axes(surface, Camera(), mode, font), 3)
                self.assertEqual(draw_axes(surface, Camera((0, 0, 100)),
                                           mode, font), 0)
                self.assertEqual(surface.get_clip(), surface.get_rect())
        finally:
            pygame.font.quit()

    def test_x_toggle_preserves_pose(self):
        pygame.font.init()
        try:
            scene = Scene()
            controls = Controls()
            panel = Panel()
            controls.update(scene, [pygame.event.Event(pygame.KEYDOWN,
                            key=pygame.K_x)], defaultdict(int), 0, panel, (0, 0))
            self.assertFalse(scene.axes_visible)
            self.assertEqual(scene.position, Scene().position)
            self.assertEqual(scene.angles, Scene().angles)
        finally:
            pygame.font.quit()


class ObjTests(unittest.TestCase):
    def load_text(self, text):
        import tempfile
        from pathlib import Path
        from renderx.obj_loader import load_obj
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.obj"
            path.write_text(text)
            return load_obj(path)

    def test_polygon_closure_unique_edges_and_normalization(self):
        text = "v 10 20 0\nv 14 20 0\nv 14 24 0\nv 10 24 0\n"
        mesh = self.load_text(text + "f 1 2 3 4\nf 4 3 2 1\n")
        self.assertEqual(mesh.edges, [(0, 1), (0, 3), (1, 2), (2, 3)])
        for actual, expected in [(mesh.vertices[0], (-1, -1, 0)),
                                 (mesh.vertices[2], (1, 1, 0))]:
            for value, target in zip(actual, expected):
                self.assertAlmostEqual(value, target)

    def test_all_face_formats_comments_and_ignored_commands(self):
        vertices = "v 0 0 0\nv 1 0 0\nv 0 1 0\n"
        for face in ["1 2 3", "1/1 2/2 3/3", "1//1 2//2 3//3",
                     "1/1/1 2/2/2 3/3/3"]:
            mesh = self.load_text(vertices + "vt 0 0\nvn 0 0 1\ng demo\n\n# comment\n"
                                  + "f " + face + " # triangle\n")
            self.assertEqual(len(mesh.edges), 3)

    def test_bad_files(self):
        vertices = "v 0 0 0\nv 1 0 0\nv 0 1 0\n"
        for text in ["", "# comment", vertices, "v nan 0 0\nf 1 2 3",
                     "v x 0 0", "v 1 2", "v 0 0 0\nv 0 0 0\nv 0 0 0\nf 1 2 3"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.load_text(text)
        for face in ["0 2 3", "-1 2 3", "1 2 9", "1 2", "1 1 2",
                     "one 2 3", "1/ 2 3", "1/2/3/4 2 3"]:
            with self.subTest(face=face), self.assertRaises(ValueError):
                self.load_text(vertices + "f " + face)

    def test_sample_and_failed_load_preserve_state(self):
        from renderx.obj_loader import load_obj, SAMPLE_OBJ
        from renderx.app import load_sample
        from renderx.models import make_models
        mesh = load_obj(SAMPLE_OBJ)
        self.assertEqual(len(mesh.vertices), 10)
        self.assertEqual(len(mesh.edges), 17)
        scene, models = Scene(), make_models()
        load_sample(scene, models)
        self.assertEqual(scene.shape, "OBJ house")
        scene.move(.5, .5)
        before = (scene.position, models[scene.shape])
        message = load_sample(scene, models, SAMPLE_OBJ.parent / "missing.obj")
        self.assertIn("failed", message)
        self.assertEqual((scene.position, models[scene.shape]), before)

    def test_o_requests_load_without_breaking_number_keys(self):
        pygame.font.init()
        try:
            controls, scene = Controls(), Scene()
            controls.update(scene, [pygame.event.Event(pygame.KEYDOWN,
                            key=pygame.K_o)], defaultdict(int), 0, Panel(), (0, 0))
            self.assertTrue(controls.load_requested)
            self.assertEqual(scene.shape, "Cube")
        finally:
            pygame.font.quit()


class ClippingTests(unittest.TestCase):
    def test_visible_hidden_crossing_reversed_and_boundary(self):
        from renderx.clipping import clip_edge_near
        a, b = (0, 0, -1), (2, 4, 1)
        front = clip_edge_near(a, b, .5)
        self.assertEqual(front, ((1.5, 3, .5), b))
        self.assertEqual(clip_edge_near(b, a, .5), (b, (1.5, 3, .5)))
        self.assertIsNone(clip_edge_near(a, (2, 4, -.5)))
        self.assertEqual(clip_edge_near((0, 0, .1), b), ((0, 0, .1), b))
        self.assertEqual(clip_edge_near((0, 0, 1), b), ((0, 0, 1), b))

    def test_tiny_denominator_and_invalid_points(self):
        from renderx.clipping import clip_edge_near
        result = clip_edge_near((0, 0, .1 - 1e-14), (2, 4, .1 + 1e-14))
        self.assertAlmostEqual(result[0][0], 1)
        self.assertAlmostEqual(result[0][1], 2)
        self.assertEqual(result[0][2], .1)
        self.assertIsNone(clip_edge_near((float('nan'), 0, 1), (0, 0, 2)))

    def test_projection_accepts_plane_and_crossing_edge(self):
        from renderx.camera import project_point
        self.assertIsNotNone(project_point((0, 0, .1)))
        for mode in ["Perspective", "Orthographic"]:
            self.assertIsNotNone(Camera().project_edge((0, 0, -1), (1, 1, 1), mode))
            self.assertIsNone(Camera().project_edge((0, 0, -1), (1, 1, 0), mode))

    def test_render_models_and_axes_through_camera(self):
        from renderx import config
        from renderx.models import make_models
        from renderx.renderer import draw_wireframe
        from renderx.axes import draw_axes
        from renderx.obj_loader import load_obj, SAMPLE_OBJ
        pygame.font.init()
        try:
            screen = pygame.Surface((config.WIDTH, config.HEIGHT))
            font = pygame.font.Font(None, 21)
            models = make_models()
            models['OBJ'] = load_obj(SAMPLE_OBJ)
            for mesh in models.values():
                for mode in ["Perspective", "Orthographic"]:
                    for depth in [5, 1, .1, 0, -1, -3]:
                        scene = Scene(position=(0, 0, depth), projection=mode)
                        drawn = draw_wireframe(screen, mesh, scene, Camera())
                        self.assertGreaterEqual(drawn, 0)
                        if depth == -3:
                            self.assertEqual(drawn, 0)
                        if depth == 0:
                            self.assertGreater(drawn, 0)
                    draw_axes(screen, Camera((0, 0, 5.5)), mode, font)
        finally:
            pygame.font.quit()


class ScreenshotTests(unittest.TestCase):
    def test_png_contents_folder_creation_and_collision(self):
        import tempfile
        from pathlib import Path
        from datetime import datetime
        from unittest.mock import patch
        from renderx.screenshots import save_screenshot
        with tempfile.TemporaryDirectory() as folder:
            screen = pygame.Surface((32, 24))
            screen.fill((21, 110, 207))
            pygame.draw.line(screen, (255, 0, 0), (0, 0), (31, 23))
            directory = Path(folder) / "screenshots"
            with patch('renderx.screenshots.datetime') as clock:
                clock.now.return_value = datetime(2026, 9, 17, 18, 30, 45)
                first = save_screenshot(screen, directory)
                before = first.read_bytes()
                second = save_screenshot(screen, directory)
            self.assertEqual(first.name, 'renderx_2026-09-17_18-30-45.png')
            self.assertEqual(second.name, 'renderx_2026-09-17_18-30-45_01.png')
            self.assertEqual(first.read_bytes(), before)
            loaded = pygame.image.load(str(second))
            self.assertEqual(pygame.image.tostring(loaded, 'RGB'),
                             pygame.image.tostring(screen, 'RGB'))

    def test_export_error_is_reported_without_crashing(self):
        from unittest.mock import patch
        from renderx.app import export_frame
        pygame.font.init()
        try:
            panel = Panel()
            with patch('renderx.app.save_screenshot', side_effect=PermissionError('denied')):
                export_frame(pygame.Surface((20, 20)), panel)
            self.assertIn('Screenshot failed', panel.message)
        finally:
            pygame.font.quit()

    def test_f12_request_clears_next_frame(self):
        pygame.font.init()
        try:
            controls, scene, panel = Controls(), Scene(), Panel()
            controls.update(scene, [pygame.event.Event(pygame.KEYDOWN,
                            key=pygame.K_F12)], defaultdict(int), 0, panel, (0, 0))
            self.assertTrue(controls.screenshot_requested)
            controls.update(scene, [], defaultdict(int), 0, panel, (0, 0))
            self.assertFalse(controls.screenshot_requested)
        finally:
            pygame.font.quit()

    def test_app_exports_new_frame_after_toggles_and_load(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from renderx.app import run
        from renderx.screenshots import save_screenshot
        from renderx import config
        key = lambda value: pygame.event.Event(pygame.KEYDOWN, key=value)
        frames = [[], [key(pygame.K_p), key(pygame.K_x), key(pygame.K_o),
                       key(pygame.K_F12)], [pygame.event.Event(pygame.QUIT)]]
        with tempfile.TemporaryDirectory() as folder:
            captures = []
            def capture(screen):
                path = save_screenshot(screen, folder)
                captures.append(path)
                return path
            with patch('pygame.event.get', side_effect=frames), \
                 patch('renderx.app.save_screenshot', side_effect=capture):
                run()
            self.assertEqual(len(captures), 1)
            self.assertEqual(pygame.image.load(str(captures[0])).get_size(),
                             (1360, 900))
            self.assertFalse(pygame.display.get_init())
