"""Persistent user settings management with local JSON storage, validation, and recovery."""
from dataclasses import dataclass, field, asdict
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict


def get_config_dir() -> Path:
    """Return standard user configuration directory for the current platform."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        if base:
            path = Path(base) / "RenderX"
        else:
            path = Path.home() / "AppData" / "Roaming" / "RenderX"
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / "RenderX"
    else:
        base = os.environ.get("XDG_CONFIG_HOME")
        if base:
            path = Path(base) / "renderx"
        else:
            path = Path.home() / ".config" / "renderx"
    path.mkdir(parents=True, exist_ok=True)
    return path


DEFAULT_KEY_BINDINGS = {
    "move_forward": "w",
    "move_backward": "s",
    "strafe_left": "a",
    "strafe_right": "d",
    "turn_left": "left",
    "turn_right": "right",
    "sprint": "shift",
    "fire": "space",
    "weapon_1": "1",
    "weapon_2": "2",
    "weapon_3": "3",
    "xray_toggle": "f8",
    "inspect_vertex": "v",
    "pause": "escape",
}


@dataclass
class Settings:
    theme: str = "Dark"
    resolution_w: int = 1360
    resolution_h: int = 900
    fullscreen: bool = False
    ui_scale: float = 1.0
    fov: float = 60.0
    mouse_sensitivity: float = 1.0
    invert_y: bool = False
    master_volume: float = 0.8
    sfx_volume: float = 0.8
    ambient_volume: float = 0.4
    render_style: str = "Wireframe"
    show_fps: bool = True
    reduced_motion: bool = False
    reduced_flash: bool = False
    first_run_tour_completed: bool = False
    difficulty: str = "NORMAL"
    key_bindings: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_KEY_BINDINGS))

    def reset_keys_to_default(self) -> None:
        self.key_bindings = dict(DEFAULT_KEY_BINDINGS)


class SettingsService:
    """Manages serialization, loading, and safe recovery of settings."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or get_config_dir()
        self.settings_file = self.config_dir / "settings.json"
        self.current = self.load()

    def load(self) -> Settings:
        if not self.settings_file.exists():
            return Settings()
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return Settings()

            # Filter valid attributes
            valid_fields = {f.name for f in Settings.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_fields}
            settings = Settings(**filtered)
            self._validate(settings)
            return settings
        except Exception:
            # Corrupted or malformed file -> return safe defaults
            return Settings()

    def save(self, settings: Settings | None = None) -> None:
        if settings is not None:
            self.current = settings
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            temp_file = self.config_dir / "settings.json.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.current), f, indent=2)
            temp_file.replace(self.settings_file)
        except Exception:
            pass

    def _validate(self, s: Settings) -> None:
        """Clamp numeric ranges and ensure allowed enum choices."""
        s.ui_scale = max(0.75, min(2.0, float(s.ui_scale)))
        s.fov = max(30.0, min(110.0, float(s.fov)))
        s.mouse_sensitivity = max(0.1, min(5.0, float(s.mouse_sensitivity)))
        s.master_volume = max(0.0, min(1.0, float(s.master_volume)))
        s.sfx_volume = max(0.0, min(1.0, float(s.sfx_volume)))
        s.ambient_volume = max(0.0, min(1.0, float(s.ambient_volume)))
        if s.difficulty not in ("RELAXED", "NORMAL", "HARD"):
            s.difficulty = "NORMAL"
        if s.theme not in ("Dark", "Light", "High-Contrast", "Colorblind-Safe"):
            s.theme = "Dark"
        if s.render_style not in ("Wireframe", "Wireframe + vertices", "Depth-fade", "Solid", "X-ray"):
            s.render_style = "Wireframe"


# Singleton instance
settings_service = SettingsService()
