"""Check the live-pixel window, resized layout, mouse mapping, and capture size."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from renderx.app import run
from renderx.camera import Camera
from renderx.dashboard import SIZE, Dashboard
from renderx.input import Controls
from renderx.models import make_library
from renderx.scene import Scene
from renderx.ui import Panel, fonts
from renderx.ui.theme import METRICS
from renderx.window import WindowView, initial_size


class WindowTests(unittest.TestCase):
    def setUp(self):
        # Other Pygame tests may quit and reinitialize SDL while cached font
        # wrappers still refer to the previous font subsystem instance.
        fonts.clear_cache()
        pygame.init()
        pygame.font.init()

    def tearDown(self):
        fonts.clear_cache()
        pygame.quit()

    def test_initial_size_respects_minimum_layout_and_desktop(self):
        for desktop in ((1366, 768), (1920, 1080), (1536, 864), (1024, 768)):
            width, height = initial_size(desktop)
            self.assertGreaterEqual(width, METRICS["min_width"])
            self.assertGreaterEqual(height, METRICS["min_height"])
            self.assertLessEqual(width, desktop[0])
            self.assertLessEqual(height, desktop[1])
            self.assertLessEqual(width, SIZE[0])
            self.assertLessEqual(height, SIZE[1])

    def test_dynamic_canvas_keeps_pointer_and_button_coordinates_sharp(self):
        scene, models, controls = Scene(), make_library(), Controls()
        dashboard = Dashboard(Panel())
        for size in ((1024, 640), (1280, 720), (1920, 1080)):
            canvas = pygame.Surface(size)
            dashboard.active_destination = "Explore"
            dashboard.draw(canvas, models["Cube"], scene, models, Camera(),
                           60, (0, 0))
            view = WindowView(size, canvas_size=size)
            self.assertEqual(view.rect, pygame.Rect(0, 0, *size))
            logical = dashboard.buttons[("destination", "Challenges")].center
            event = view.event(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=logical))
            dashboard.events([event], scene, models, None, controls)
            self.assertEqual(dashboard.active_destination, "Challenges")
            self.assertEqual(view.point(logical), logical)
            dashboard.active_destination = "Explore"

    def test_hidpi_display_maps_pointer_and_drag_to_canvas_pixels(self):
        view = WindowView((1920, 1080), canvas_size=(960, 540))
        event = view.event(pygame.event.Event(
            pygame.MOUSEMOTION, pos=(960, 540), rel=(20, 10), buttons=(1, 0, 0)))
        self.assertEqual(event.pos, (480, 270))
        self.assertEqual(event.rel, (10, 5))

    def test_resizing_switching_screenshot_and_quit_use_live_canvas(self):
        probe = Dashboard(Panel())
        models, scene = make_library(), Scene()
        target = pygame.Surface((1024, 648))
        probe.active_destination = "Shooter"
        probe.draw(target, models["Cube"], scene, models, Camera(), 60, (0, 0))
        tab_position = probe.buttons[("destination", "Challenges")].center
        frames = [[],
                  [pygame.event.Event(pygame.VIDEORESIZE, w=980, h=648,
                                      size=(980, 648))],
                  [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                      pos=tab_position)],
                  [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F12)],
                  [pygame.event.Event(pygame.QUIT)]]
        captures = []

        def capture(surface):
            captures.append(surface.get_size())
            return Path("resize-capture.png")

        with patch("pygame.event.get", side_effect=frames), \
                patch("renderx.app.save_screenshot", side_effect=capture), \
                patch("renderx.app.initial_size", return_value=SIZE):
            run(skip_landing=True)
        self.assertEqual(captures, [(METRICS["min_width"], 648)])
        self.assertFalse(pygame.display.get_init())

    def test_shooter_launch_failure_restores_renderx_and_shows_reason(self):
        panel = Panel()
        probe = Dashboard(panel)
        probe.active_destination = "Shooter"
        target = pygame.Surface(SIZE)
        probe.draw(target, make_library()["Cube"], Scene(), make_library(),
                   Camera(), 60, (0, 0))
        launch_position = probe.buttons[("shooter_launch",)].center
        sent_launch = False
        sent_quit = False
        original_draw = Dashboard.draw

        def draw_and_exit_after_failure(dashboard, *args, **kwargs):
            nonlocal sent_launch, sent_quit
            result = original_draw(dashboard, *args, **kwargs)
            if dashboard.active_destination == "Shooter" and not sent_launch:
                pygame.event.post(pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=launch_position))
                sent_launch = True
            elif sent_launch and dashboard.active_destination == "Explore" and not sent_quit:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                sent_quit = True
            return result

        with patch("renderx.app.Panel", return_value=panel), \
                patch("renderx.shooter.run_shooter",
                      side_effect=RuntimeError("OpenGL 3.3 unavailable")) as launch, \
                patch("renderx.app.initial_size", return_value=SIZE), \
                patch.object(Dashboard, "draw", draw_and_exit_after_failure):
            run(mode="shooter")

        self.assertTrue(sent_quit)
        self.assertEqual(launch.call_count, 1)
        self.assertIn("OpenGL 3.3 unavailable", panel.message)
        self.assertFalse(pygame.display.get_init())


if __name__ == "__main__":
    unittest.main()
