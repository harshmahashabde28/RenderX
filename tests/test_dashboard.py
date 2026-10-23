"""Exercise the responsive editor shell with headless Pygame surfaces."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path
from math import radians
import tempfile
import unittest
from unittest.mock import patch

import pygame

from renderx import config, theme
from renderx.app import run
from renderx.camera import Camera
from renderx.dashboard import Dashboard, SIZE
from renderx.input import Controls
from renderx.models import make_library
from renderx.scene import Scene
from renderx.ui import Panel, fonts
from renderx.ui.theme import METRICS


class DashboardTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        theme.apply("dark")
        self.panel = Panel()
        self.ui = Dashboard(self.panel)
        self.scene = Scene()
        self.models = make_library()
        self.controls = Controls()

    def tearDown(self):
        fonts.clear_cache()
        pygame.quit()

    def draw(self, size=SIZE, destination="Explore"):
        self.ui.active_destination = destination
        target = pygame.Surface(size)
        self.ui.draw(target, self.models.get(self.scene.shape, self.models["Cube"]),
                     self.scene, self.models, Camera(), 60, (0, 0), dt=1 / 60)
        return target

    def click(self, action, *, size=SIZE, scene=None, maze=None, quest=None):
        scene = self.scene if scene is None else scene
        self.ui.layout(scene, self.models, quest, maze, size)
        self.assertIn(action, self.ui.buttons)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.ui.buttons[action].center)
        return self.ui.events([event], scene, self.models, quest,
                              self.controls, maze)

    def test_destinations_and_tab_cycle_use_the_live_shell(self):
        target = self.draw((1280, 720))
        self.assertEqual(target.get_size(), (1280, 720))
        self.assertEqual(self.ui.view_rect, pygame.Rect(250, 68, 724, 612))
        self.assertEqual(set(self.ui.app_layout.navigation),
                         {"Explore", "Challenges", "Maze", "Shooter"})
        self.click(("destination", "Challenges"), size=(1280, 720))
        self.assertEqual(self.ui.active_destination, "Challenges")
        for expected in ("Maze", "Shooter", "Explore", "Challenges"):
            self.ui.events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB)],
                           self.scene, self.models, None, self.controls)
            self.assertEqual(self.ui.active_destination, expected)

    def test_shared_audio_controls_fit_and_update_at_minimum_width(self):
        class AudioStub:
            def __init__(self):
                self.volume = 0.25
                self.music_muted = False
                self.saved = 0

            def play(self, name):
                return True

            def set_volume(self, value, *, persist=True):
                self.volume = value
                return value

            def save_settings(self):
                self.saved += 1

            def toggle_music(self):
                self.music_muted = not self.music_muted
                return self.music_muted

        audio = AudioStub()
        self.ui.set_audio(audio)
        self.draw((1024, 720))
        layout = self.ui.app_layout
        self.assertLessEqual(layout.audio_slider.right, layout.music_toggle.left)
        self.assertLessEqual(layout.music_toggle.right, layout.import_obj.left)

        self.click(("audio_volume",), size=(1024, 720))
        self.ui.events([pygame.event.Event(pygame.MOUSEBUTTONUP, button=1,
                                           pos=(0, 0))], self.scene,
                       self.models, None, self.controls)
        self.assertAlmostEqual(audio.volume, 0.5, places=2)
        self.assertEqual(audio.saved, 1)

        self.click(("music_toggle",), size=(1024, 720))
        self.assertTrue(audio.music_muted)

    def test_mesh_catalog_scrolls_and_sample_import_uses_existing_action(self):
        for index, name in enumerate(self.models):
            self.ui.scene_panel.scroll = max(0, index - 4)
            self.ui.layout(self.scene, self.models)
            action = ("shape", name)
            self.assertIn(action, self.ui.buttons)
            self.click(action)
            self.assertEqual(self.scene.shape, name)
        output = self.click(("load_sample",))
        self.controls.update(self.scene, output, {}, 0, self.panel, (-100, -100))
        self.assertTrue(self.controls.load_requested)

    def test_transform_slider_numeric_field_and_display_actions(self):
        self.ui.layout(self.scene, self.models)
        angle_action = ("slider", "rotation", 0)
        position_action = ("slider", "position", 2)
        self.assertIn(angle_action, self.ui.buttons)
        before = self.scene.angles[0]
        self.click(angle_action)
        self.assertNotEqual(self.scene.angles[0], before)

        field = ("field", "rotation", 0)
        self.click(field)
        for key, character in ((pygame.K_4, "4"), (pygame.K_5, "5")):
            self.ui.events([pygame.event.Event(pygame.KEYDOWN, key=key,
                                               unicode=character)],
                           self.scene, self.models, None, self.controls)
        self.ui.events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN,
                                           unicode="\r")],
                       self.scene, self.models, None, self.controls)
        self.assertAlmostEqual(self.scene.angles[0], radians(45), places=6)

        self.click(("projection_panel", "Orthographic"))
        self.assertEqual(self.scene.projection, "Orthographic")
        before_axes = self.scene.axes_visible
        self.click(("axes",))
        self.assertNotEqual(self.scene.axes_visible, before_axes)
        self.click(("reset",))
        self.assertEqual(self.scene.position, Scene().position)

    def test_render_mode_help_theme_and_focus_shortcuts(self):
        self.ui.layout(self.scene, self.models)
        self.click(("render_menu",))
        self.assertEqual(self.ui.render_mode, "Hidden line")
        self.ui.events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1)],
                       self.scene, self.models, None, self.controls)
        self.assertTrue(self.ui.help_open)
        self.ui.events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
                       self.scene, self.models, None, self.controls)
        self.assertFalse(self.ui.help_open)
        self.ui.events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F6)],
                       self.scene, self.models, None, self.controls)
        self.assertIsNotNone(self.ui.focused_action)

        original = theme.mode()
        with tempfile.TemporaryDirectory() as temporary:
            with patch("renderx.theme._SETTING", Path(temporary) / "settings.json"):
                self.click(("theme",))
                expected = "light" if original == "dark" else "dark"
                self.assertEqual(theme.mode(), expected)
                self.assertEqual(config.APP_BG,
                                 theme.palette(expected)["CANVAS"])
        theme.apply(original)

    def test_render_mode_dropdown_supports_click_keyboard_and_outside_close(self):
        self.draw()
        dropdown = self.ui.buttons[("render_mode_select",)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=dropdown)],
            self.scene, self.models, None, self.controls)
        self.assertTrue(self.ui.render_mode_open)

        self.draw()
        option = self.ui.buttons[("render_mode_option", "Solid")].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=option)],
            self.scene, self.models, None, self.controls)
        self.assertEqual(self.ui.render_mode, "Solid")
        self.assertFalse(self.ui.render_mode_open)

        self.draw()
        dropdown = self.ui.buttons[("render_mode_select",)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=dropdown)],
            self.scene, self.models, None, self.controls)
        self.ui.events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP),
                        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
                       self.scene, self.models, None, self.controls)
        self.assertEqual(self.ui.render_mode, "Hidden line")
        self.assertFalse(self.ui.render_mode_open)

        self.draw()
        dropdown = self.ui.buttons[("render_mode_select",)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=dropdown)],
            self.scene, self.models, None, self.controls)
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 68))],
            self.scene, self.models, None, self.controls)
        self.assertFalse(self.ui.render_mode_open)

    def test_double_clicking_a_slider_restores_that_value_to_default(self):
        self.ui.layout(self.scene, self.models)
        self.scene.angles = (0.0, self.scene.angles[1], self.scene.angles[2])
        action = ("slider", "rotation", 0)
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, clicks=2,
            pos=self.ui.buttons[action].center)],
            self.scene, self.models, None, self.controls)
        self.assertAlmostEqual(self.scene.angles[0], config.DEFAULT_ANGLES[0])

    def test_focus_loss_prevents_control_actions_and_mouse_maps_to_view_only(self):
        self.ui.layout(self.scene, self.models, size=(1280, 720))
        centre = self.ui.view_rect.center
        self.assertEqual(self.ui.map_position(centre), (410, 370))
        self.assertEqual(self.ui.map_position((20, 200)), (-100, -100))
        before = self.scene.position
        self.ui.events([pygame.event.Event(pygame.WINDOWFOCUSLOST)], self.scene,
                       self.models, None, self.controls)
        action = ("slider", "position", 2)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.ui.buttons[action].center)
        self.ui.events([event], self.scene, self.models, None, self.controls)
        self.assertEqual(self.scene.position, before)

    def test_collapsible_docks_and_all_requested_canvas_sizes(self):
        for size in ((1024, 640), (1280, 720), (1920, 1080)):
            target = self.draw(size)
            self.assertEqual(target.get_size(), size)
            self.assertGreaterEqual(self.ui.view_rect.width, 380)
            self.assertEqual(target.get_at((0, 0))[:3],
                             theme.palette()["SURFACE_1"])
        self.ui.layout(self.scene, self.models)
        self.click(("dock_collapse", "left"))
        self.assertTrue(self.ui.left_collapsed)
        self.click(("dock", "left"))
        self.assertFalse(self.ui.left_collapsed)
        self.click(("dock_collapse", "right"))
        self.assertTrue(self.ui.right_collapsed)

    def test_splitters_resize_both_docks_without_covering_the_view(self):
        self.ui.layout(self.scene, self.models, size=(1280, 720))
        initial_left = self.ui.app_layout.left_dock.width
        splitter = self.ui.buttons[("splitter", "left")].center
        self.ui.events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                           pos=splitter)], self.scene,
                       self.models, None, self.controls)
        self.ui.events([pygame.event.Event(pygame.MOUSEMOTION,
                                           pos=(splitter[0] + 40, splitter[1]),
                                           rel=(40, 0), buttons=(1, 0, 0))],
                       self.scene, self.models, None, self.controls)
        self.assertGreater(self.ui.left_width, initial_left)
        self.assertGreaterEqual(self.ui.left_width,
                                METRICS["dock_min"])

        self.ui.layout(self.scene, self.models, size=(1280, 720))
        initial_right = self.ui.app_layout.right_dock.width
        splitter = self.ui.buttons[("splitter", "right")].center
        self.ui.events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                           pos=splitter)], self.scene,
                       self.models, None, self.controls)
        self.ui.events([pygame.event.Event(pygame.MOUSEMOTION,
                                           pos=(splitter[0] - 40, splitter[1]),
                                           rel=(-40, 0), buttons=(1, 0, 0))],
                       self.scene, self.models, None, self.controls)
        self.assertGreater(self.ui.right_width, initial_right)
        self.ui.layout(self.scene, self.models, size=(1280, 720))
        self.assertGreaterEqual(self.ui.view_rect.width, 380)

    def test_shooter_launch_hands_off_and_returns_to_previous_destination(self):
        self.ui.layout(self.scene, self.models)
        self.click(("destination", "Shooter"))
        self.assertEqual(self.ui.previous_destination, "Explore")
        self.click(("shooter_launch",))
        self.assertTrue(self.ui.shooter_requested)

        probe = Dashboard(Panel())
        probe.active_destination = "Shooter"
        target = pygame.Surface(SIZE)
        probe.draw(target, self.models["Cube"], self.scene, self.models,
                   Camera(), 60, (0, 0))
        launch_position = probe.buttons[("shooter_launch",)].center
        frames = [[], [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                           pos=launch_position)],
                  [pygame.event.Event(pygame.QUIT)]]
        with patch("pygame.event.get", side_effect=frames), \
                patch("renderx.shooter.run_shooter", return_value=True) as launch, \
                patch("renderx.app.initial_size", return_value=SIZE):
            run(mode="shooter")
        self.assertEqual(launch.call_count, 1)
        self.assertFalse(pygame.display.get_init())

    def test_standard_view_aliases_and_clickable_axis_gizmo(self):
        self.ui.layout(self.scene, self.models)
        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_1,
            mod=pygame.KMOD_CTRL, unicode="1")], self.scene, self.models,
            None, self.controls)
        self.assertAlmostEqual(self.scene.angles[0], 0.0)
        self.assertAlmostEqual(self.scene.angles[1], 0.0)
        self.assertAlmostEqual(self.scene.angles[2], 0.0)

        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_KP3,
            mod=pygame.KMOD_CTRL, unicode="")], self.scene, self.models,
            None, self.controls)
        right_angle = self.scene.angles[1]
        self.assertAlmostEqual(min(right_angle, 2 * 3.141592653589793 - right_angle),
                               3.141592653589793 / 2)

        self.draw()
        action = ("view_axis", "Z", 1)
        self.assertIn(action, self.ui.buttons)
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1,
            pos=self.ui.buttons[action].center)], self.scene, self.models,
            None, self.controls)
        self.assertAlmostEqual(self.scene.angles[0], 0.0)
        self.assertAlmostEqual(self.scene.angles[1], 0.0)

    def test_navigation_drag_continues_after_pointer_leaves_view(self):
        self.ui.active_destination = "Explore"
        self.draw((1280, 720))
        start = self.ui.view_rect.center
        outside = (self.ui.view_rect.right + 80, start[1] + 10)
        events = [
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=start),
            pygame.event.Event(pygame.WINDOWLEAVE),
            pygame.event.Event(pygame.MOUSEMOTION, pos=outside, rel=(32, 12),
                               buttons=(1, 0, 0)),
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=outside),
        ]
        mapped = self.ui.events(events, self.scene, self.models, None,
                                self.controls)
        self.controls.update(self.scene, mapped, {}, 0, self.panel,
                             self.ui.map_position(outside))
        self.assertNotEqual(self.scene.angles, Scene().angles)
        self.assertIsNone(self.controls.drag)

    def test_file_menu_releases_toolbar_press_and_closes_on_outside_click(self):
        self.draw()
        toolbar_position = self.ui.buttons[("toolbar_open_obj",)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=toolbar_position)],
            self.scene, self.models, None, self.controls)
        self.assertTrue(self.ui.file_menu_open)

        self.draw()
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONUP, button=1, pos=toolbar_position)],
            self.scene, self.models, None, self.controls)
        self.assertIsNone(self.ui.pressed)

        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 68))],
            self.scene, self.models, None, self.controls)
        self.assertFalse(self.ui.file_menu_open)
        self.assertTrue(self.controls.focused)

    def test_file_menu_preferences_route_opens_modal_without_focusing_canvas(self):
        self.draw()
        toolbar_position = self.ui.buttons[("toolbar_open_obj",)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=toolbar_position)],
            self.scene, self.models, None, self.controls)
        self.draw()
        position = self.ui.buttons[("file_menu", "preferences")].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position)],
            self.scene, self.models, None, self.controls)
        self.assertFalse(self.ui.file_menu_open)
        self.assertTrue(self.ui.preferences_open)
        self.assertFalse(self.controls.focused)

    def test_global_shortcuts_replace_open_popovers(self):
        self.draw()
        toolbar_position = self.ui.buttons[("toolbar_open_obj",)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=toolbar_position)],
            self.scene, self.models, None, self.controls)
        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_F1)], self.scene,
            self.models, None, self.controls)
        self.assertFalse(self.ui.file_menu_open)
        self.assertTrue(self.ui.help_open)

        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_ESCAPE)], self.scene,
            self.models, None, self.controls)
        self.draw()
        dropdown_position = self.ui.buttons[("render_mode_select",)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=dropdown_position)],
            self.scene, self.models, None, self.controls)
        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_F1)], self.scene,
            self.models, None, self.controls)
        self.assertFalse(self.ui.render_mode_open)
        self.assertTrue(self.ui.help_open)

        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_ESCAPE)], self.scene,
            self.models, None, self.controls)
        self.draw()
        toolbar_position = self.ui.buttons[("toolbar_open_obj",)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=toolbar_position)],
            self.scene, self.models, None, self.controls)
        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_COMMA, mod=pygame.KMOD_CTRL,
            unicode=",")], self.scene, self.models, None, self.controls)
        self.assertFalse(self.ui.file_menu_open)
        self.assertTrue(self.ui.preferences_open)

    def test_help_about_shortcut_and_escape_routes(self):
        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_F1)], self.scene,
            self.models, None, self.controls)
        self.draw()
        position = self.ui.buttons[("help", "about")].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=3, pos=position)], self.scene,
            self.models, None, self.controls)
        self.assertTrue(self.ui.help_open)
        self.assertFalse(self.ui.about_open)
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position)], self.scene,
            self.models, None, self.controls)
        self.assertFalse(self.ui.help_open)
        self.assertTrue(self.ui.about_open)
        self.assertFalse(self.controls.focused)
        view = self.ui.view_rect.center
        self.ui.events([
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=view),
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=3, pos=view),
        ], self.scene, self.models, None, self.controls)
        self.assertTrue(self.ui.about_open)
        self.assertFalse(self.ui.context_menu_open)

        self.draw()
        position = self.ui.buttons[("about", "shortcuts")].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position)], self.scene,
            self.models, None, self.controls)
        self.assertFalse(self.ui.about_open)
        self.assertTrue(self.ui.help_open)
        self.ui.events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_ESCAPE)], self.scene,
            self.models, None, self.controls)
        self.assertFalse(self.ui.help_open)
        self.assertTrue(self.controls.focused)

    def test_right_click_opens_view_and_object_context_menus(self):
        self.draw()
        position = self.ui.view_rect.center
        self.ui.events([
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=position),
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=3, pos=position),
        ], self.scene, self.models, None, self.controls)
        self.assertTrue(self.ui.context_menu_open)
        self.assertFalse(self.controls.focused)

        self.draw()
        front = self.ui.buttons[("view_axis", "Z", 1)].center
        self.ui.events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=front)],
            self.scene, self.models, None, self.controls)
        self.assertFalse(self.ui.context_menu_open)
        self.assertAlmostEqual(self.scene.angles[0], 0.0)
        self.assertAlmostEqual(self.scene.angles[1], 0.0)

        self.draw()
        cube = self.ui.buttons[("shape", "Cube")].center
        self.ui.events([
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=cube),
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=3, pos=cube),
        ], self.scene, self.models, None, self.controls)
        self.assertTrue(self.ui.context_menu_open)
        self.assertEqual(self.ui.context_menu_target, "Cube")

    def test_right_drag_still_uses_the_selected_navigation_preset(self):
        self.draw((1280, 720))
        start = self.ui.view_rect.center
        events = [
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=start),
            pygame.event.Event(pygame.MOUSEMOTION, pos=(start[0] + 20, start[1] + 8),
                               rel=(20, 8), buttons=(0, 0, 1)),
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=3,
                               pos=(start[0] + 20, start[1] + 8)),
        ]
        mapped = self.ui.events(events, self.scene, self.models, None,
                                self.controls)
        self.controls.update(self.scene, mapped, {}, 0, self.panel,
                             self.ui.map_position((start[0] + 20, start[1] + 8)))

        self.assertFalse(self.ui.context_menu_open)
        self.assertEqual(self.scene.angles, config.DEFAULT_ANGLES)
        self.assertNotEqual(self.scene.position, (0.0, 0.0, 5.0))

    def test_preferences_persist_navigation_preset_and_numeric_tab_traverses(self):
        original = theme.navigation_preset()
        with tempfile.TemporaryDirectory() as temporary:
            settings = Path(temporary) / "settings.json"
            with patch("renderx.theme._SETTING", settings):
                self.ui.events([pygame.event.Event(
                    pygame.KEYDOWN, key=pygame.K_COMMA,
                    mod=pygame.KMOD_CTRL, unicode=",")], self.scene,
                    self.models, None, self.controls)
                self.draw()
                self.assertTrue(self.ui.preferences_open)
                choice = self.ui.buttons[("preference", "RenderX Classic")].center
                self.ui.events([pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=choice)],
                    self.scene, self.models, None, self.controls)
                self.assertEqual(theme.navigation_preset(), "RenderX Classic")
                data = settings.read_text(encoding="utf-8")
                self.assertIn("RenderX Classic", data)
                self.ui.events([pygame.event.Event(
                    pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="\x1b")],
                    self.scene, self.models, None, self.controls)
                self.assertFalse(self.ui.preferences_open)
        theme._navigation_preset = original

        self.ui.layout(self.scene, self.models)
        first = ("field", "rotation", 0)
        self.click(first)
        self.ui.events([pygame.event.Event(pygame.KEYDOWN,
                                           key=pygame.K_TAB, unicode="\t")],
                       self.scene, self.models, None, self.controls)
        self.assertEqual(self.ui.focused_field, ("field", "rotation", 1))


if __name__ == "__main__":
    unittest.main()
