"""Known-answer checks; no display or Pygame required for these maths tests."""
import math
import unittest
from renderx import config
from renderx.camera import Camera, project_point
from renderx.mesh import Mesh
from renderx.models import make_models
from renderx.scene import Scene
from renderx.transform import rotate_x, rotate_y, rotate_z, transform_vertex


class CoreTests(unittest.TestCase):
    def assertPoint(self, actual, expected):
        for value, target in zip(actual, expected):
            self.assertAlmostEqual(value, target, places=6)

    def test_shapes(self):
        models = make_models()
        for name, counts in [("Cube", (8, 12)), ("Pyramid", (5, 8)),
                             ("Rectangular prism", (8, 12))]:
            mesh = models[name]
            self.assertEqual((len(mesh.vertices), len(mesh.edges)), counts)
        cube = models["Cube"]
        for a, b in cube.edges:
            self.assertEqual(sum(x != y for x, y in
                                 zip(cube.vertices[a], cube.vertices[b])), 1)

    def test_bad_meshes(self):
        for vertices, edges in [([], []), ([(0, 0, math.nan)], []),
                                ([(0, 0, 0)], [(0, 2)]),
                                ([(0, 0, 0)], [(0, 0.5)]),
                                ([(0, 0, 0)], [(0, 0)]),
                                ([(0, 0, 0), (1, 0, 0)], [(0, 1), (1, 0)])]:
            with self.subTest(vertices=vertices, edges=edges):
                with self.assertRaises(ValueError):
                    Mesh(vertices, edges)

    def test_known_rotations(self):
        self.assertPoint(rotate_x((0, 1, 0), math.pi / 2), (0, 0, 1))
        self.assertPoint(rotate_y((0, 0, 1), math.pi / 2), (1, 0, 0))
        self.assertPoint(rotate_z((1, 0, 0), math.pi / 2), (0, 1, 0))

    def test_rotation_preserves_length_and_full_turn(self):
        for rotate in (rotate_x, rotate_y, rotate_z):
            point = (0.5, -2, 3)
            self.assertPoint(rotate(point, math.tau), point)
            self.assertAlmostEqual(math.dist(rotate(point, .73), (0, 0, 0)),
                                   math.dist(point, (0, 0, 0)))

    def test_transform_order(self):
        scene = Scene(angles=(0, 0, math.pi / 2), position=(1, 2, 5), scale=2)
        self.assertPoint(transform_vertex((1, 0, 0), scene), (1, 4, 5))

    def test_original_vertices_preserved(self):
        mesh = make_models()["Cube"]
        original = mesh.vertices.copy()
        scene = Scene()
        for _ in range(1000):
            scene.rotate(.01, .02, .03)
            for point in mesh.vertices:
                transform_vertex(point, scene)
        self.assertEqual(mesh.vertices, original)

    def test_perspective(self):
        self.assertPoint(project_point((1, 1, 5), (390, 350)), (480, 260))
        self.assertPoint(project_point((1, 1, 10), (390, 350)), (435, 305))

    def test_bad_projection_inputs(self):
        for point in [(1, 1, 0), (1, 1, -1), (1, 1, .1),
                      (math.nan, 1, 5), (1, math.inf, 5), (1, 1, math.inf)]:
            self.assertIsNone(project_point(point))

    def test_camera(self):
        camera = Camera((1, 2, 3))
        self.assertPoint(camera.relative_point((2, 4, 8)), (1, 2, 5))
        self.assertEqual(camera.project((2, 4, 8)), project_point((1, 2, 5)))

    def test_bounds_reset_and_safe_depth(self):
        scene = Scene(shape="Pyramid")
        scene.move(100, -100, -100)
        scene.resize(-100)
        self.assertEqual(scene.position, (1, -1, config.MIN_DEPTH))
        self.assertEqual(scene.scale, config.MIN_SCALE)
        scene.move(-100, 100, 100)
        scene.resize(100)
        self.assertEqual(scene.position, (-1, 1, config.MAX_DEPTH))
        self.assertEqual(scene.scale, config.MAX_SCALE)
        scene.reset()
        self.assertEqual(scene, Scene(shape="Pyramid"))
        for mesh in make_models().values():
            radius = max(math.dist(v, (0, 0, 0)) for v in mesh.vertices)
            self.assertGreater(config.MIN_DEPTH - radius * config.MAX_SCALE,
                               config.NEAR_DEPTH)
