"""Persisted appearance preference backed by the UI design tokens."""

import json
import os
from pathlib import Path
import sys

from renderx import config
from renderx.input_map import DEFAULT_NAVIGATION_PRESET, NAVIGATION_PRESETS
from renderx.ui.theme import palette


def settings_path(platform_name=None, home=None, environ=None):
    """Return RenderX's settings file under the platform's user config folder."""
    platform_name = sys.platform if platform_name is None else platform_name
    home = Path.home() if home is None else Path(home)
    environ = os.environ if environ is None else environ
    if platform_name == "win32":
        local_app_data = environ.get("LOCALAPPDATA")
        root = Path(local_app_data) if local_app_data else home / "AppData" / "Local"
    elif platform_name == "darwin":
        root = home / "Library" / "Application Support"
    else:
        config_home = environ.get("XDG_CONFIG_HOME")
        root = Path(config_home) if config_home else home / ".config"
    return root / "RenderX" / "settings.json"


_SETTING = settings_path()
_mode = "dark"
_navigation_preset = DEFAULT_NAVIGATION_PRESET
_recent_files = []
_welcome_seen = False


def mode():
    return _mode


def navigation_preset():
    return _navigation_preset


def recent_files():
    return tuple(_recent_files)


def welcome_seen():
    return _welcome_seen


def mark_welcome_seen():
    global _welcome_seen
    _welcome_seen = True
    _save_settings()


def remember_file(path):
    """Keep a short, de-duplicated Open Recent list in the normal settings file."""
    global _recent_files
    value = str(Path(path).expanduser().resolve())
    _recent_files = [value, *(item for item in _recent_files if item != value)][:8]
    _save_settings()


def set_navigation_preset(value):
    global _navigation_preset
    _navigation_preset = (value if value in NAVIGATION_PRESETS
                          else DEFAULT_NAVIGATION_PRESET)
    _save_settings()
    return _navigation_preset


def apply(value):
    global _mode
    _mode = "light" if value == "light" else "dark"
    for key, color in palette(_mode).items():
        setattr(config, key, color)
    return _mode


def load():
    global _navigation_preset, _recent_files, _welcome_seen
    try:
        settings = json.loads(_SETTING.read_text(encoding="utf-8"))
    except (OSError, ValueError, AttributeError):
        settings = {}
    if not isinstance(settings, dict):
        settings = {}
    _navigation_preset = settings.get("navigation_preset", DEFAULT_NAVIGATION_PRESET)
    if _navigation_preset not in NAVIGATION_PRESETS:
        _navigation_preset = DEFAULT_NAVIGATION_PRESET
    raw_recent = settings.get("recent_files", [])
    _recent_files = [str(path) for path in raw_recent if isinstance(path, str)][:8] \
        if isinstance(raw_recent, list) else []
    _welcome_seen = bool(settings.get("welcome_seen", False))
    return apply(settings.get("theme", "dark"))


def toggle():
    new_mode = apply("light" if _mode == "dark" else "dark")
    _save_settings()
    return new_mode


def _save_settings():
    try:
        _SETTING.parent.mkdir(parents=True, exist_ok=True)
        _SETTING.write_text(json.dumps({
            "theme": _mode,
            "navigation_preset": _navigation_preset,
            "recent_files": _recent_files,
            "welcome_seen": _welcome_seen,
        }, indent=2),
                            encoding="utf-8")
    except OSError:
        pass
