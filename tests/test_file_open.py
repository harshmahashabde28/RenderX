"""Desktop file-open behavior stays safe and keeps a short recent list."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from renderx.app import load_obj_file
from renderx.models import make_library
from renderx.obj_loader import SAMPLE_OBJ
from renderx.scene import Scene


class FileOpenTests(unittest.TestCase):
    def test_open_obj_adds_selects_and_remembers_mesh(self):
        scene, models = Scene(), make_library()
        with tempfile.TemporaryDirectory() as temporary:
            settings = Path(temporary) / "settings.json"
            with patch("renderx.theme._SETTING", settings), \
                    patch("renderx.theme._recent_files", []):
                result = load_obj_file(SAMPLE_OBJ, scene, models)
                self.assertEqual(result, "Opened house.obj")
                self.assertEqual(scene.shape, "house")
                self.assertIn("house", models)
                self.assertEqual(json.loads(settings.read_text())["recent_files"],
                                 [str(SAMPLE_OBJ.resolve())])

    def test_invalid_obj_keeps_current_scene_and_models(self):
        scene, models = Scene(), make_library()
        original_shape = scene.shape
        original_names = set(models)
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing.obj"
            result = load_obj_file(missing, scene, models)
        self.assertIn("Could not open missing.obj", result)
        self.assertEqual(scene.shape, original_shape)
        self.assertEqual(set(models), original_names)


if __name__ == "__main__":
    unittest.main()
