"""Unit tests for the new UI system, layout engine, widgets, and settings."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import tempfile
from pathlib import Path
import unittest
import pygame

from renderx.ui.theme import set_theme, THEMES, current_theme
from renderx.ui.layout import Rect, Box, Column, Row, Grid, Align
from renderx.ui.widgets import Button, ToggleButton, TabBar, Slider, Label, Card, ProgressBar
from renderx.services.settings import Settings, SettingsService
from renderx.app.state_machine import StateMachine, AppState
from renderx.app.screens.menu_screen import MainMenuScreen
from renderx.app.screens.settings_screen import SettingsScreen
from renderx.app.screens.about_screen import AboutScreen
from renderx.app.screens.tour_screen import TourScreen


class UILayoutTests(unittest.TestCase):
    def test_rect_collision(self):
        r = Rect(10, 20, 100, 50)
        self.assertTrue(r.collidepoint((50, 40)))
        self.assertFalse(r.collidepoint((5, 40)))
        self.assertEqual(r.right, 110)
        self.assertEqual(r.bottom, 70)

    def test_column_layout(self):
        col = Column(0, 0, 200, spacing=10)
        r1 = col.add(100, 30)
        r2 = col.add(150, 40)
        self.assertEqual(r1.y, 0)
        self.assertEqual(r2.y, 40)
        self.assertEqual(col.total_height, 80)

    def test_row_layout(self):
        row = Row(0, 0, 50, spacing=10)
        r1 = row.add(60, 30)
        r2 = row.add(80, 40)
        self.assertEqual(r1.x, 0)
        self.assertEqual(r2.x, 70)
        self.assertEqual(row.total_width, 150)


class SettingsTests(unittest.TestCase):
    def test_settings_save_and_safe_recovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            svc = SettingsService(config_dir=Path(tmpdir))
            s = svc.load()
            s.fov = 75.0
            s.theme = "Light"
            svc.save(s)

            loaded = svc.load()
            self.assertEqual(loaded.fov, 75.0)
            self.assertEqual(loaded.theme, "Light")

            # Corrupt file test
            bad_file = Path(tmpdir) / "settings.json"
            bad_file.write_text("{malformed json", encoding="utf-8")
            recovered = svc.load()
            self.assertEqual(recovered.theme, "Dark")  # default recovered


class ScreensHeadlessRenderTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.surface = pygame.Surface((1360, 900))

    def tearDown(self):
        pygame.quit()

    def test_all_screens_layout_and_draw_at_multiple_sizes(self):
        sizes = [(800, 600), (960, 600), (1280, 720), (1360, 900), (1920, 1080)]
        for w, h in sizes:
            surf = pygame.Surface((w, h))

            # Menu
            menu = MainMenuScreen(lambda dest: None, lambda: None)
            menu.layout(w, h)
            menu.draw(surf)

            # Settings
            settings = SettingsScreen(lambda: None)
            settings.layout(w, h)
            settings.draw(surf)

            # About
            about = AboutScreen(lambda: None)
            about.layout(w, h)
            about.draw(surf)

            # Tour
            tour = TourScreen(lambda: None)
            tour.layout(w, h)
            tour.draw(surf)


if __name__ == "__main__":
    unittest.main()
