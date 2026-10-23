"""Keep preferences in each platform's normal user configuration folder."""

import unittest

from renderx.theme import settings_path


class SettingsPathTests(unittest.TestCase):
    def test_windows_uses_local_app_data(self):
        path = settings_path("win32", r"C:\Users\Riley",
                             {"LOCALAPPDATA": r"C:\Users\Riley\Local"})
        self.assertEqual(path.as_posix(), "C:/Users/Riley/Local/RenderX/settings.json")

    def test_macos_uses_application_support(self):
        path = settings_path("darwin", "/Users/riley", {})
        self.assertEqual(path.as_posix(),
                         "/Users/riley/Library/Application Support/RenderX/settings.json")

    def test_linux_respects_xdg_config_home(self):
        path = settings_path("linux", "/home/riley",
                             {"XDG_CONFIG_HOME": "/tmp/config"})
        self.assertEqual(path.as_posix(), "/tmp/config/RenderX/settings.json")


if __name__ == "__main__":
    unittest.main()
