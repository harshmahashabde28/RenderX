"""Regression coverage for the landing-first navigation flow."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest
from unittest.mock import patch

import pygame

from renderx import theme
from renderx.camera import Camera
from renderx.dashboard import Dashboard
from renderx.input import Controls
from renderx.maze import MazeState
from renderx.models import make_library
from renderx.scene import Scene
from renderx.ui import Panel, fonts
from renderx.ui import theme as ui_theme
from renderx.ui.components.button import icon_button_rect
from renderx.ui import icons, layout


class LaunchFlowTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        theme.apply("dark")
        self.dashboard = Dashboard(Panel())
        self.models = make_library()
        self.scene = Scene()
        self.controls = Controls()
        self.maze = MazeState(seed=7)

    def tearDown(self):
        fonts.clear_cache()
        pygame.quit()

    def draw(self, destination="Landing", size=(1280, 720)):
        self.dashboard.active_destination = destination
        target = pygame.Surface(size)
        self.dashboard.draw(target, self.models[self.scene.shape], self.scene,
                            self.models, Camera(), 60, (0, 0), maze_state=self.maze,
                            dt=1 / 60)
        return target

    def press(self, key, mod=0):
        return self.dashboard.events(
            [pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod)],
            self.scene, self.models, None, self.controls, self.maze)

    def click(self, action):
        self.draw(self.dashboard.active_destination)
        rect = self.dashboard.buttons[action]
        return self.dashboard.events(
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                pos=rect.center)],
            self.scene, self.models, None, self.controls, self.maze)

    def test_landing_enter_opens_explore_and_escape_is_safe(self):
        self.draw()
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.dashboard.active_destination, "Landing")
        self.press(pygame.K_RETURN)
        self.assertEqual(self.dashboard.active_destination, "Explore")
        self.assertEqual(self.dashboard._transition_elapsed, 0.0)
        self.draw("Explore")
        self.assertIn(("destination", "Explore"), self.dashboard.buttons)

    def test_landing_tabs_focus_actions_and_space_activates(self):
        self.draw()
        self.press(pygame.K_TAB)
        self.assertEqual(self.dashboard.landing_focus, ("landing", "open_obj"))
        self.press(pygame.K_TAB)
        self.assertEqual(self.dashboard.landing_focus, ("landing", "shortcuts"))
        self.press(pygame.K_SPACE)
        self.assertTrue(self.dashboard.help_open)

    def test_landing_has_no_skip_preference_or_focus_target(self):
        self.draw()
        self.assertNotIn(("landing", "dont_show_again"), self.dashboard.buttons)
        self.assertEqual(self.dashboard._landing_action_order(), (
            ("landing", "explore"), ("landing", "open_obj"),
            ("landing", "shortcuts"), ("landing", "about")))

    def test_landing_is_the_default_launch_destination(self):
        from renderx import app

        self.assertEqual(app._initial_destination(skip_landing=False, mode=None),
                         "Landing")
        self.assertEqual(app._initial_destination(skip_landing=True, mode=None),
                         "Explore")
        self.assertEqual(app._initial_destination(skip_landing=False, mode="maze"),
                         "Maze")

    def test_tab_widths_fit_real_text_and_page_shortcuts(self):
        geometry = layout.build_layout((1024, 640))
        label = "Challenge"
        challenge_rect = geometry.navigation["Challenges"]
        required = fonts.font("control").size(label)[0] + ui_theme.SPACE["md"] * 2
        self.assertGreaterEqual(challenge_rect.width, required)
        self.draw("Explore", (1024, 640))
        self.press(pygame.K_2, pygame.KMOD_CTRL | pygame.KMOD_ALT)
        self.assertEqual(self.dashboard.active_destination, "Challenges")

    def test_home_confirms_for_an_active_maze_and_cancel_keeps_it_open(self):
        self.draw("Maze")
        self.press(pygame.K_h, pygame.KMOD_CTRL | pygame.KMOD_SHIFT)
        self.assertEqual(self.dashboard.active_destination, "Maze")
        self.assertTrue(self.dashboard.confirm_home_open)
        self.click(("home_confirmation", "cancel"))
        self.assertEqual(self.dashboard.active_destination, "Maze")
        self.assertFalse(self.dashboard.confirm_home_open)
        self.press(pygame.K_h, pygame.KMOD_CTRL | pygame.KMOD_SHIFT)
        self.click(("home_confirmation", "leave"))
        self.assertEqual(self.dashboard.active_destination, "Landing")

    def test_panel_state_is_isolated_per_destination_and_restored(self):
        self.draw("Explore")
        self.dashboard.left_collapsed = True
        self.dashboard.left_width = 274
        self.dashboard.scene_panel.scroll = 8
        self.dashboard.open_sections = {"objects"}
        self.dashboard._set_destination("Challenges")
        self.assertFalse(self.dashboard.left_collapsed)
        self.assertIsNone(self.dashboard.left_width)
        self.assertEqual(self.dashboard.scene_panel.scroll, 0)
        self.assertEqual(self.dashboard.open_sections, {"transform", "display"})

        self.dashboard.right_collapsed = True
        self.dashboard.scene_panel.scroll = 2
        self.dashboard._set_destination("Explore")
        self.assertTrue(self.dashboard.left_collapsed)
        self.assertFalse(self.dashboard.right_collapsed)
        self.assertEqual(self.dashboard.left_width, 274)
        self.assertEqual(self.dashboard.scene_panel.scroll, 8)
        self.assertEqual(self.dashboard.open_sections, {"objects"})

    def test_shooter_status_uses_visible_torus_counts(self):
        from unittest.mock import patch

        captured = {}
        def record(_surface, _rect, items, *_args, **_kwargs):
            captured["items"] = tuple(items)

        with patch("renderx.dashboard.draw_status", side_effect=record):
            self.draw("Shooter")
        status = dict(captured["items"])
        torus = self.models["Torus"]
        self.assertEqual(status["OBJ"], "Torus")
        self.assertEqual(status["V"], len(torus.vertices))
        self.assertEqual(status["E"], len(torus.edges))
        self.assertEqual(status["F"], len(torus.faces or ()))

    def test_mode_flags_are_forwarded_to_the_application(self):
        from renderx.__main__ import main

        with patch("renderx.app.run") as run:
            self.assertEqual(main(["--skip-landing"]), 0)
            run.assert_called_once_with(skip_landing=True, mode=None)
        with patch("renderx.app.run") as run:
            self.assertEqual(main(["--mode", "challenge"]), 0)
            run.assert_called_once_with(skip_landing=False, mode="challenge")


class IconLayoutTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()

    def tearDown(self):
        fonts.clear_cache()
        pygame.quit()

    def test_every_svg_and_mesh_icon_is_safe_at_small_and_large_sizes(self):
        icon_names = [path.stem for path in icons._ASSET_DIRECTORY.glob("*.svg")]
        icon_names.extend(f"shape:{name}" for name in make_library())
        icon_names.append("brand")
        for name in icon_names:
            for side in (12, 16, 20, 24, 32):
                target = pygame.Surface((side + 32, side + 32), pygame.SRCALPHA)
                rect = pygame.Rect(16, 16, side, side)
                icons.draw_icon(target, name, rect, (245, 245, 245))
                pixels = target.get_bounding_rect(min_alpha=1)
                self.assertFalse(pixels.colliderect(pygame.Rect(0, 0, 16, 16)))
                self.assertGreaterEqual(pixels.left - rect.left, 1, (name, side))
                self.assertGreaterEqual(pixels.top - rect.top, 1, (name, side))
                self.assertGreaterEqual(rect.right - pixels.right, 1, (name, side))
                self.assertGreaterEqual(rect.bottom - pixels.bottom, 1, (name, side))
                self.assertLessEqual(abs(pixels.centerx - rect.centerx), 1,
                                     (name, side, pixels, rect))
                self.assertLessEqual(abs(pixels.centery - rect.centery), 1,
                                     (name, side, pixels, rect))

    def test_real_dashboard_icon_buttons_stay_inside_their_hit_rects(self):
        dashboard = Dashboard(Panel())
        models = make_library()
        scene = Scene()
        for destination in ("Explore", "Challenges", "Maze", "Shooter"):
            target = pygame.Surface((1280, 720))
            dashboard.active_destination = destination
            dashboard.draw(target, models[scene.shape], scene, models,
                           Camera(), 60, (0, 0), maze_state=MazeState(seed=3))
            for action, placement in dashboard.icon_placements.items():
                button = placement["button"]
                icon_rect = placement["icon"]
                canvas = pygame.Surface((1280, 720), pygame.SRCALPHA)
                name = "brand" if action == ("home",) else "box"
                icons.draw_icon(canvas, name, icon_rect, (245, 245, 245))
                pixels = canvas.get_bounding_rect(min_alpha=1)
                self.assertGreaterEqual(pixels.left - button.left, 1,
                                        (destination, action, pixels, button))
                self.assertGreaterEqual(pixels.top - button.top, 1,
                                        (destination, action, pixels, button))
                self.assertGreaterEqual(button.right - pixels.right, 1,
                                        (destination, action, pixels, button))
                self.assertGreaterEqual(button.bottom - pixels.bottom, 1,
                                        (destination, action, pixels, button))
                if placement["align"] == "center":
                    label_width = fonts.font("control").size(
                        placement["label"])[0]
                    gap = ui_theme.SPACE["sm"]
                    if label_width and icon_rect.centerx != button.centerx:
                        content = pygame.Rect(
                            icon_rect.left, button.centery - icon_rect.height // 2,
                            icon_rect.width + gap + label_width,
                            icon_rect.height)
                        self.assertLessEqual(
                            abs(content.centerx - button.centerx), 1,
                            (destination, action, content, button))
                    else:
                        self.assertLessEqual(
                            abs(icon_rect.centerx - button.centerx), 1,
                            (destination, action, icon_rect, button))
                    self.assertLessEqual(abs(icon_rect.centery - button.centery), 1,
                                         (destination, action, icon_rect, button))


if __name__ == "__main__":
    unittest.main()
