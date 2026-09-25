"""Real Pygame surfaces and event handlers, using SDL's headless driver."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
from collections import defaultdict
from unittest.mock import patch
import unittest
import pygame
from renderx import config
from renderx.app import run
from renderx.camera import Camera
from renderx.input import Controls, SHAPE_KEYS
from renderx.models import make_models
from renderx.renderer import draw_wireframe
from renderx.scene import Scene
from renderx.ui import Panel


def event(kind, **attributes):
    return pygame.event.Event(kind, attributes)


class InteractionTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        self.scene, self.controls, self.panel = Scene(), Controls(), Panel()

    def tearDown(self):
        pygame.quit()

    def update(self, events=(), keys=(), pos=(200, 200), modifiers=0):
        pressed = defaultdict(int, {key: 1 for key in keys})
        return self.controls.update(self.scene, events, pressed, .04,
                                    self.panel, pos, modifiers)

    def test_each_rotation_key_and_release(self):
        for key, axis, sign in [(pygame.K_UP, 0, 1), (pygame.K_DOWN, 0, -1),
                                (pygame.K_RIGHT, 1, 1), (pygame.K_LEFT, 1, -1),
                                (pygame.K_e, 2, 1), (pygame.K_q, 2, -1)]:
            self.scene.angles = (1, 1, 1)
            self.update(keys=[key])
            self.assertGreater((self.scene.angles[axis] - 1) * sign, 0)
            before = self.scene.angles
            self.update()
            self.assertEqual(self.scene.angles, before)

    def test_each_translation_key(self):
        for key, axis, sign in [(pygame.K_d, 0, 1), (pygame.K_a, 0, -1),
                                (pygame.K_w, 1, 1), (pygame.K_s, 1, -1),
                                (pygame.K_PAGEUP, 2, -1),
                                (pygame.K_PAGEDOWN, 2, 1)]:
            self.scene.reset()
            before = self.scene.position[axis]
            self.update(keys=[key])
            self.assertGreater((self.scene.position[axis] - before) * sign, 0)

    def test_scale_keys_and_bounds(self):
        for key in [pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS]:
            self.scene.reset()
            self.update(keys=[key])
            self.assertGreater(self.scene.scale, 1)
        for key in [pygame.K_MINUS, pygame.K_KP_MINUS]:
            self.scene.reset()
            self.update(keys=[key])
            self.assertLess(self.scene.scale, 1)
        for _ in range(300):
            self.update(keys=[pygame.K_MINUS])
        self.assertEqual(self.scene.scale, config.MIN_SCALE)

    def test_opposite_and_unknown_keys(self):
        self.update(keys=[pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP,
                          pygame.K_DOWN, pygame.K_q, pygame.K_e, pygame.K_w,
                          pygame.K_s, pygame.K_a, pygame.K_d, pygame.K_EQUALS,
                          pygame.K_MINUS, pygame.K_PAGEUP, pygame.K_PAGEDOWN,
                          pygame.K_F8])
        self.assertEqual(self.scene, Scene())

    def test_keyboard_selection_reset_override_motion(self):
        for key, name in SHAPE_KEYS.items():
            self.scene.resize(.2)
            self.update([event(pygame.KEYDOWN, key=key)], [pygame.K_w])
            self.assertEqual(self.scene, Scene(shape=name))
        self.scene.move(1, 1)
        self.controls.drag = "xy"
        self.update([event(pygame.KEYDOWN, key=pygame.K_r)])
        self.assertEqual(self.scene, Scene(shape="Rectangular prism"))
        self.assertIsNone(self.controls.drag)

    def test_mouse_selection_reset(self):
        for name in ["Cube", "Pyramid", "Rectangular prism", "Reset"]:
            self.scene.resize(.2)
            self.update([event(pygame.MOUSEBUTTONDOWN, button=1,
                               pos=self.panel.buttons[name].center)])
            selected = "Rectangular prism" if name == "Reset" else name
            self.assertEqual(self.scene, Scene(shape=selected))
            self.assertIsNone(self.controls.drag)

    def drag(self, button, modifiers=0):
        self.update([event(pygame.MOUSEBUTTONDOWN, button=button, pos=(200, 200)),
                     event(pygame.MOUSEMOTION, pos=(220, 180), rel=(20, -20))],
                    modifiers=modifiers)

    def test_mouse_rotates_all_axes_and_releases(self):
        self.drag(1)
        self.assertGreater(self.scene.angles[0], config.DEFAULT_ANGLES[0])
        self.assertGreater(self.scene.angles[1], config.DEFAULT_ANGLES[1])
        self.update([event(pygame.MOUSEBUTTONUP, button=1, pos=(220, 180))])
        self.assertIsNone(self.controls.drag)
        self.drag(3)
        self.assertGreater(self.scene.angles[2], 0)

    def test_both_pan_gestures(self):
        for button, modifiers in [(2, 0), (1, pygame.KMOD_SHIFT)]:
            self.controls.cancel_drag()
            self.scene.reset()
            self.drag(button, modifiers)
            self.assertEqual(self.scene.angles, config.DEFAULT_ANGLES)
            self.assertEqual(self.scene.position, (.1, .1, 5))

    def test_wheel_and_panel_isolation(self):
        self.update([event(pygame.MOUSEWHEEL, y=100)])
        self.assertEqual(self.scene.scale, config.MAX_SCALE)
        self.update([event(pygame.MOUSEWHEEL, y=-100)])
        self.assertEqual(self.scene.scale, config.MIN_SCALE)
        self.scene.reset()
        pos = (config.VIEW_WIDTH + 5, 400)
        self.update([event(pygame.MOUSEWHEEL, y=1),
                     event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos),
                     event(pygame.MOUSEMOTION, pos=(200, 200), rel=(50, 50))], pos=pos)
        self.assertEqual(self.scene, Scene())

    def test_focus_minimise_and_leaving_viewport(self):
        for kind in [pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED]:
            self.drag(1)
            self.update([event(kind)], [pygame.K_w])
            self.assertIsNone(self.controls.drag)
            before = self.scene.position
            self.update(keys=[pygame.K_w])
            self.assertEqual(self.scene.position, before)
            self.update([event(pygame.WINDOWFOCUSGAINED)])
            self.update(keys=[pygame.K_w])
            self.assertGreater(self.scene.position[1], before[1])
        self.drag(1)
        self.update([event(pygame.MOUSEMOTION, pos=(900, 200), rel=(680, 0))])
        self.assertIsNone(self.controls.drag)

    def test_exit_routes(self):
        for close in [event(pygame.QUIT), event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
                      event(pygame.MOUSEBUTTONDOWN, button=1,
                            pos=self.panel.buttons["Exit"].center)]:
            self.assertFalse(self.update([close]))

    def test_render_all_shapes_and_clip(self):
        for name, mesh in make_models().items():
            self.scene.select(name)
            self.screen.fill((255, 0, 0))
            self.assertEqual(draw_wireframe(self.screen, mesh, self.scene, Camera()),
                             len(mesh.edges))
            self.assertEqual(self.screen.get_at((config.VIEW_WIDTH + 1, 300))[:3],
                             (255, 0, 0))
            self.assertEqual(self.screen.get_clip(), self.screen.get_rect())
            self.panel.draw(self.screen, self.scene, mesh, 60)

    def test_behind_camera_edges_skipped(self):
        count = draw_wireframe(self.screen, make_models()["Cube"], self.scene,
                               Camera((0, 0, 100)))
        self.assertEqual(count, 0)

    def test_real_app_loop_each_exit_and_cleanup(self):
        for close in [event(pygame.QUIT), event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
                      event(pygame.MOUSEBUTTONDOWN, button=1,
                            pos=(1277,29))]:
            frames = [[], [event(pygame.KEYDOWN, key=pygame.K_2)],
                      [event(pygame.KEYDOWN, key=pygame.K_3)], [close]]
            with patch("pygame.event.get", side_effect=frames):
                with patch('renderx.app.initial_size', return_value=(1360, 900)):
                    run()
            self.assertFalse(pygame.display.get_init())
