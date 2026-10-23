"""Unit tests for the software rendering engine, camera, culling, and math paths."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import math
import random
import unittest
import pygame

from renderx import config
from renderx.core.camera import Camera
from renderx.core.clipping import (
    clip_line_2d_liang_barsky,
    clip_line_2d_cohen_sutherland,
)
from renderx.core.models import make_cube
from renderx.core.shapes import sphere, torus
from renderx.core.scene import Scene
from renderx.engine.culling import (
    is_within_distance,
    calculate_face_normal,
    is_backface,
)
from renderx.engine.spatial import SpatialGrid
from renderx.engine.fast_math import (
    has_numpy,
    batch_transform_pure,
    batch_transform_numpy,
    batch_transform,
)
from renderx.engine.renderer import draw_wireframe, VIEWPORT
from renderx.engine.styles import RenderStyle


class CameraEngineTests(unittest.TestCase):
    def test_camera_zero_rotation_matches_legacy(self):
        cam = Camera(position=(1.0, 2.0, 3.0))
        pt = (4.0, 7.0, 11.0)
        self.assertEqual(cam.to_camera_space(pt), (3.0, 5.0, 8.0))
        self.assertEqual(cam.relative_point(pt), (3.0, 5.0, 8.0))

    def test_camera_yaw_and_pitch_vectors(self):
        cam = Camera(position=(0.0, 0.0, 0.0), yaw=0.0, pitch=0.0)
        fwd = cam.forward_vector()
        self.assertAlmostEqual(fwd[0], 0.0)
        self.assertAlmostEqual(fwd[1], 0.0)
        self.assertAlmostEqual(fwd[2], 1.0)

        # 90 degrees yaw (turn right) -> forward points along +X
        cam.yaw = math.pi / 2.0
        fwd = cam.forward_vector()
        self.assertAlmostEqual(fwd[0], 1.0)
        self.assertAlmostEqual(fwd[2], 0.0)

        # Pitch 90 degrees down -> forward points along -Y
        cam.yaw = 0.0
        cam.pitch = math.pi / 2.0
        fwd = cam.forward_vector()
        self.assertAlmostEqual(fwd[1], -1.0)
        self.assertAlmostEqual(fwd[2], 0.0)


class Clipping2DTests(unittest.TestCase):
    def test_fully_inside_segment(self):
        res = clip_line_2d_liang_barsky((10, 10), (50, 50), 0, 0, 100, 100)
        self.assertIsNotNone(res)
        p1, p2 = res
        self.assertAlmostEqual(p1[0], 10)
        self.assertAlmostEqual(p1[1], 10)
        self.assertAlmostEqual(p2[0], 50)
        self.assertAlmostEqual(p2[1], 50)

    def test_partially_outside_segment_clipped_to_box(self):
        res = clip_line_2d_liang_barsky((-50, 50), (150, 50), 0, 0, 100, 100)
        self.assertIsNotNone(res)
        p1, p2 = res
        self.assertAlmostEqual(p1[0], 0.0)
        self.assertAlmostEqual(p1[1], 50.0)
        self.assertAlmostEqual(p2[0], 100.0)
        self.assertAlmostEqual(p2[1], 50.0)

    def test_fully_outside_segment_rejected(self):
        res = clip_line_2d_liang_barsky((-100, 10), (-10, 50), 0, 0, 100, 100)
        self.assertIsNone(res)

    def test_cohen_sutherland_matches_liang_barsky(self):
        lb = clip_line_2d_liang_barsky((-20, 20), (120, 80), 0, 0, 100, 100)
        cs = clip_line_2d_cohen_sutherland((-20, 20), (120, 80), 0, 0, 100, 100)
        self.assertIsNotNone(lb)
        self.assertIsNotNone(cs)
        for (x1, y1), (x2, y2) in zip(lb, cs):
            self.assertAlmostEqual(x1, x2, places=5)
            self.assertAlmostEqual(y1, y2, places=5)


class CullingAndSpatialTests(unittest.TestCase):
    def test_distance_cull(self):
        cam = (0.0, 0.0, 0.0)
        self.assertTrue(is_within_distance((5.0, 0.0, 5.0), cam, 10.0))
        self.assertFalse(is_within_distance((10.0, 0.0, 10.0), cam, 10.0))

    def test_backface_culling(self):
        # Triangle in XY plane facing towards origin camera (normal points in -Z direction)
        v0 = (0.0, 1.0, 5.0)
        v1 = (1.0, -1.0, 5.0)
        v2 = (-1.0, -1.0, 5.0)
        camera_front = (0.0, 0.0, 0.0)
        camera_behind = (0.0, 0.0, 10.0)

        # Facing towards camera_front (normal points towards -Z, viewer is at Z=0)
        self.assertFalse(is_backface(v0, v1, v2, camera_front))
        # Facing away from camera_behind (viewer is at Z=10)
        self.assertTrue(is_backface(v0, v1, v2, camera_behind))

    def test_spatial_grid_query(self):
        grid = SpatialGrid[str](cell_size=2.0)
        grid.insert("wall_1", 0.0, 0.0, 1.0, 1.0)
        grid.insert("wall_2", 10.0, 10.0, 11.0, 11.0)

        # Query near wall_1
        near = grid.query_radius(0.5, 0.5, 1.0)
        self.assertIn("wall_1", near)
        self.assertNotIn("wall_2", near)

        # Query near wall_2
        far = grid.query_radius(10.5, 10.5, 1.0)
        self.assertIn("wall_2", far)
        self.assertNotIn("wall_1", far)


class MathEquivalenceTests(unittest.TestCase):
    def test_pure_vs_numpy_random_inputs(self):
        if not has_numpy():
            self.skipTest("NumPy is not installed.")

        random.seed(42)
        # Generate 100 random vertices
        vertices = [
            (random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5))
            for _ in range(100)
        ]
        angles = (random.uniform(-math.pi, math.pi),
                  random.uniform(-math.pi, math.pi),
                  random.uniform(-math.pi, math.pi))
        pos = (random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(1, 20))
        scale = random.uniform(0.5, 3.0)

        pure_res = batch_transform_pure(vertices, scale, angles, pos)
        numpy_res = batch_transform_numpy(vertices, scale, angles, pos)

        self.assertEqual(len(pure_res), len(numpy_res))
        for p, n in zip(pure_res, numpy_res):
            for pv, nv in zip(p, n):
                self.assertAlmostEqual(pv, nv, places=6)


class RenderStylesTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.surface = pygame.Surface((800, 600))
        self.camera = Camera((0.0, 0.0, 0.0))
        self.scene = Scene(position=(0.0, 0.0, 5.0))
        self.mesh = make_cube()

    def tearDown(self):
        pygame.quit()

    def test_all_render_styles_draw_without_error(self):
        for style in RenderStyle:
            drawn = draw_wireframe(
                self.surface,
                self.mesh,
                self.scene,
                self.camera,
                render_style=style,
                clear=True,
            )
            self.assertGreater(drawn, 0)


if __name__ == "__main__":
    unittest.main()
