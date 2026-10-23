"""Text-fit behavior for compact button labels."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest

import pygame

from renderx.ui import fonts
from renderx.input_map import help_rows
from renderx.ui.components.overlay import draw_overlay
from renderx.ui.theme import SPACE


class FontLayoutTests(unittest.TestCase):
    def setUp(self):
        # Other test modules deliberately shut down and restart SDL; start this
        # fixture with clean cached typefaces just as the application does.
        fonts.clear_cache()
        pygame.init()
        pygame.font.init()
        self.surface = pygame.Surface((80, 32), pygame.SRCALPHA)

    def tearDown(self):
        fonts.clear_cache()
        pygame.quit()

    def test_omit_label_when_ellipsis_cannot_fit(self):
        before = pygame.image.tostring(self.surface, "RGBA")
        rect = fonts.draw_text(self.surface, "Collapse scene dock", (40, 16),
                               "control", (255, 255, 255), anchor="center",
                               max_width=0)

        self.assertEqual(rect.width, 0)
        self.assertEqual(pygame.image.tostring(self.surface, "RGBA"), before)

    def test_ellipsis_fits_when_width_allows_it(self):
        typeface = fonts.font("control")
        ellipsis_width = typeface.size("...")[0]
        rect = fonts.draw_text(self.surface, "Collapse scene dock", (4, 4),
                               "control", (255, 255, 255), max_width=ellipsis_width)

        self.assertEqual(rect.width, ellipsis_width)
        self.assertLessEqual(rect.width, ellipsis_width)

    def test_shortcut_overlay_fits_a_minimum_size_window_without_cutting_bindings(self):
        surface = pygame.Surface((1024, 640))
        rows = help_rows("Explore", "Signal wave", "Orbit Viewer")
        panel, _ = draw_overlay(surface, "Keyboard shortcuts", rows,
                                footer_action="Getting started")
        available = panel.width // 2 - SPACE["xxl"]

        self.assertEqual(panel.width, 920)
        self.assertLessEqual(panel.bottom, surface.get_height())
        self.assertTrue(all(fonts.font("value").size(key)[0] <= available
                            for _, key in rows))


if __name__ == "__main__":
    unittest.main()
