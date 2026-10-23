"""Bundled audio, persistent controls, and SVG icon rendering."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path
import tempfile
import unittest

import pygame

from renderx.audio import AudioManager, _SOUND_FILES
from renderx.ui.icons import draw_icon


class AudioManagerTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.temporary = tempfile.TemporaryDirectory()
        self.settings_path = Path(self.temporary.name) / "audio.json"
        self.audio = AudioManager(self.settings_path)

    def tearDown(self):
        pygame.quit()
        self.temporary.cleanup()

    def test_all_short_effects_load_and_can_play(self):
        if not self.audio.available:
            self.skipTest("No Pygame audio device is available")
        self.assertEqual(set(self.audio._sounds), set(_SOUND_FILES))
        self.assertTrue(self.audio.play("ui_click"))

    def test_destination_music_volume_and_mute_are_saved(self):
        if not self.audio.available:
            self.skipTest("No Pygame audio device is available")
        self.audio.switch_music("maze")
        self.assertEqual(self.audio.current_music, "maze")
        self.audio.set_volume(0.42)
        self.assertTrue(self.audio.toggle_music())
        self.assertFalse(self.audio.toggle_music())
        self.audio.switch_music("shooter")
        self.assertEqual(self.audio.current_music, "shooter")

        restored = AudioManager(self.settings_path)
        self.assertAlmostEqual(restored.volume, 0.42)
        self.assertFalse(restored.music_muted)
        restored.switch_music(None)

    def test_effect_and_music_files_are_bundled(self):
        asset_directory = Path(__file__).resolve().parents[1] / "assets" / "audio"
        for filename in (*_SOUND_FILES.values(), "maze_theme.ogg",
                         "shooter_theme.ogg"):
            with self.subTest(filename=filename):
                self.assertGreater((asset_directory / filename).stat().st_size, 0)


class LucideIconTests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_downloaded_svg_icons_render_in_the_requested_color(self):
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_icon(surface, "cube", pygame.Rect(4, 4, 24, 24), (40, 126, 106))
        pixels = pygame.surfarray.array3d(surface)
        alpha = pygame.surfarray.array_alpha(surface)
        self.assertGreater(int(alpha.sum()), 0)
        opaque = alpha == 255
        self.assertGreater(int(opaque.sum()), 0)
        difference = abs(pixels[opaque].astype(int) - (40, 126, 106))
        self.assertLessEqual(int(difference.max()), 2)


if __name__ == "__main__":
    unittest.main()
