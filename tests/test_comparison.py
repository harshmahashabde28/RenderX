"""Projection math shared by the interactive depth challenge."""

import unittest

from renderx.camera import Camera
from renderx.comparison import COMPARE_FOCAL_LENGTH, projected_bounds
from renderx.mesh import Mesh
from renderx.scene import Scene
from renderx.transform import transform_vertex


class ProjectionComparisonTests(unittest.TestCase):
    def test_depth_changes_perspective_size_but_not_orthographic_size(self):
        mesh = Mesh([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)],
                    [(0, 1), (1, 2), (2, 3), (3, 0)])
        camera = Camera()
        bounds = {}
        for mode in ("Perspective", "Orthographic"):
            for depth in (5, 10):
                scene = Scene(angles=(0, 0, 0), position=(0, 0, depth))
                points = [transform_vertex(vertex, scene) for vertex in mesh.vertices]
                bounds[mode, depth] = projected_bounds(
                    points, mesh.edges, camera, mode, (400, 300))
        size = lambda rect: (rect[2] - rect[0], rect[3] - rect[1])
        self.assertEqual(size(bounds["Perspective", 5]), (120, 120))
        self.assertEqual(size(bounds["Perspective", 10]), (60, 60))
        self.assertEqual(size(bounds["Orthographic", 5]), (120, 120))
        self.assertEqual(size(bounds["Orthographic", 10]), (120, 120))

    def test_edges_crossing_camera_plane_are_clipped_before_bounds(self):
        camera = Camera()
        crossing = projected_bounds([(0, 0, -1), (2, 4, 1)], [(0, 1)],
                                    camera, "Perspective", (100, 200),
                                    COMPARE_FOCAL_LENGTH)
        hidden = projected_bounds([(0, 0, -2), (2, 4, -1)], [(0, 1)],
                                  camera, "Perspective", (100, 200))
        self.assertIsNotNone(crossing)
        self.assertIsNone(hidden)


if __name__ == "__main__":
    unittest.main()
