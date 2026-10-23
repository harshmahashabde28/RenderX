"""Regression checks for shared keyboard and mouse convention metadata."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest
from unittest.mock import patch

import pygame

from renderx.input_map import (DEFAULT_NAVIGATION_PRESET, EDITOR_KEYS,
                               GLOBAL_KEYS, MAZE_KEYS, MOUSE_BUTTONS,
                               MOUSE_GESTURES, SHAPE_KEYS, SHOOTER_KEYS,
                               help_rows, modifier_name, navigation_status,
                               view_shortcut)


class InputMapTests(unittest.TestCase):
    def test_existing_bindings_remain_in_the_shared_map(self):
        self.assertEqual(SHAPE_KEYS[pygame.K_1], "Cube")
        self.assertEqual(SHAPE_KEYS[pygame.K_2], "Pyramid")
        self.assertEqual(SHAPE_KEYS[pygame.K_3], "Rectangular prism")
        self.assertEqual(EDITOR_KEYS["open_sample"], pygame.K_o)
        self.assertEqual(EDITOR_KEYS["render_mode"], pygame.K_m)
        self.assertEqual(MAZE_KEYS["scan"], pygame.K_SPACE)
        self.assertEqual(SHOOTER_KEYS["fullscreen"], pygame.K_F11)

    def test_default_viewer_and_classic_mouse_presets_are_explicit(self):
        self.assertEqual(DEFAULT_NAVIGATION_PRESET, "Orbit Viewer")
        self.assertEqual(MOUSE_GESTURES["Orbit Viewer"]["orbit"],
                         MOUSE_BUTTONS["primary"])
        self.assertEqual(MOUSE_GESTURES["Orbit Viewer"]["pan"], (2, 3))
        self.assertEqual(MOUSE_GESTURES["RenderX Classic"]["z_turn"], (3,))

    def test_standard_views_keep_unmodified_shape_shortcuts(self):
        self.assertEqual(view_shortcut(pygame.K_KP1, 0), ("front", 1))
        self.assertEqual(view_shortcut(pygame.K_1, 0), None)
        self.assertEqual(view_shortcut(pygame.K_1, pygame.KMOD_CTRL), ("front", 1))
        self.assertEqual(view_shortcut(pygame.K_1,
                                       pygame.KMOD_CTRL | pygame.KMOD_SHIFT),
                         ("front", -1))
        self.assertEqual(view_shortcut(pygame.K_KP3, pygame.KMOD_CTRL), ("right", -1))

    def test_shortcut_overlay_uses_preset_and_destination_bindings(self):
        orbit = dict(help_rows("Explore", "Signal wave", "Orbit Viewer"))
        classic = dict(help_rows("Explore", "Cube", "RenderX Classic"))
        maze = dict(help_rows("Maze", "Cube", "Orbit Viewer"))
        self.assertIn("RMB drag pan", orbit["Navigation · Orbit / pan / zoom"])
        self.assertIn("RMB drag Z-turn", classic["Navigation · Orbit / pan / zoom"])
        self.assertIn("Right-click viewport / object",
                      orbit["Navigation · Open context menu"])
        self.assertIn("Shift+LMB", orbit["Navigation · Pan alias"])
        self.assertIn("Space", orbit["Animation · Signal wave play / pause"])
        self.assertIn("Signal", str(orbit))
        self.assertIn("New run", str(maze))
        self.assertEqual(orbit["Application · Close / cancel overlay"], "Esc")
        self.assertEqual(orbit["Application · Toggle fullscreen"], "F11")
        self.assertNotIn("Navigation · Reset scene pose", maze)
        self.assertNotIn("Navigation · Perspective / orthographic", maze)
        self.assertIn("RMB click menu", navigation_status("Orbit Viewer"))

    def test_platform_shortcuts_use_command_on_macos(self):
        with patch("renderx.input_map.sys.platform", "darwin"):
            self.assertEqual(modifier_name(), "Cmd")
            rows = dict(help_rows("Explore", "Cube", "Orbit Viewer"))
        self.assertEqual(rows["File · Open OBJ"], "Cmd+O")
        self.assertIn("Cmd+Shift+1", rows["Navigation · Opposite views"])


if __name__ == "__main__":
    unittest.main()
