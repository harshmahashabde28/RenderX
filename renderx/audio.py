"""Shared, optional Pygame audio for RenderX and Breakpoint."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

import pygame


_ASSET_DIRECTORY = Path(__file__).resolve().parents[1] / "assets" / "audio"
_SOUND_FILES = {
    "ui_click": "ui_click.ogg",
    "confirm": "confirm.ogg",
    "health_pickup": "confirm.ogg",
    "locked": "locked.ogg",
    "shoot": "laser.ogg",
    "enemy_shoot": "enemy_laser.ogg",
    "impact": "impact.ogg",
    "enemy_down": "enemy_down.ogg",
    "player_down": "player_down.ogg",
    "dash": "dash.ogg",
    "scan": "scan.ogg",
    "footstep": "footstep.ogg",
    "pickup": "pickup.ogg",
}
_MUSIC_FILES = {
    "maze": "maze_theme.ogg",
    "shooter": "shooter_theme.ogg",
}
_SOUND_GAINS = {
    "ui_click": 0.28,
    "confirm": 0.32,
    "health_pickup": 0.52,
    "locked": 0.3,
    "shoot": 0.16,
    "enemy_shoot": 0.12,
    "impact": 0.2,
    "enemy_down": 0.22,
    "player_down": 0.25,
    "dash": 0.24,
    "scan": 0.3,
    "footstep": 0.22,
    "pickup": 0.38,
}
_MUSIC_GAIN = 0.3


class AudioManager:
    """Load CC0 audio once, route music by destination, and keep audio optional."""

    def __init__(self, settings_path: str | Path | None = None):
        local_data = os.environ.get("LOCALAPPDATA")
        default_root = (Path(local_data) if local_data else
                        Path.home() / ".local" / "share")
        self.settings_path = Path(settings_path or default_root / "RenderX" /
                                  "audio.json")
        self.volume = 0.66
        self.music_muted = False
        self.current_music: str | None = None
        self.available = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._channels: list[tuple[pygame.mixer.Channel, float]] = []
        self._last_played: dict[str, float] = {}
        self._load_settings()
        self._initialize_mixer()

    def _initialize_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2,
                                  buffer=512)
            pygame.mixer.set_num_channels(16)
            self.available = True
        except (pygame.error, OSError):
            # Audio devices are optional. Rendering and input must remain usable.
            return

        for name, filename in _SOUND_FILES.items():
            try:
                self._sounds[name] = pygame.mixer.Sound(_ASSET_DIRECTORY / filename)
            except (pygame.error, OSError):
                continue
        self._apply_music_volume()

    def _load_settings(self) -> None:
        try:
            settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
            self.volume = max(0.0, min(1.0, float(settings.get("volume", self.volume))))
            self.music_muted = bool(settings.get("music_muted", False))
        except (OSError, TypeError, ValueError, AttributeError):
            return

    def save_settings(self) -> None:
        """Persist the user's volume and music preference outside the project."""
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings_path.write_text(
                json.dumps({"volume": self.volume,
                            "music_muted": self.music_muted}, indent=2),
                encoding="utf-8")
        except OSError:
            pass

    def set_volume(self, value: float, *, persist: bool = True) -> float:
        """Set the shared music and effects level from 0.0 through 1.0."""
        self.volume = max(0.0, min(1.0, float(value)))
        self._apply_music_volume()
        still_playing = []
        for channel, gain in self._channels:
            try:
                if channel.get_busy():
                    channel.set_volume(self.volume * gain)
                    still_playing.append((channel, gain))
            except pygame.error:
                continue
        self._channels = still_playing
        if persist:
            self.save_settings()
        return self.volume

    def toggle_music(self) -> bool:
        """Toggle background music and return whether it is now muted."""
        self.music_muted = not self.music_muted
        if self.available:
            try:
                self._apply_music_volume()
                if self.music_muted:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            except pygame.error:
                pass
        self.save_settings()
        return self.music_muted

    def switch_music(self, destination: str | None) -> None:
        """Play the destination's loop, or stop music outside game screens."""
        if destination not in _MUSIC_FILES:
            if self.available:
                try:
                    pygame.mixer.music.stop()
                except pygame.error:
                    pass
            self.current_music = None
            return
        if destination == self.current_music:
            return
        if not self.available:
            self.current_music = destination
            return
        try:
            pygame.mixer.music.load(_ASSET_DIRECTORY / _MUSIC_FILES[destination])
            self._apply_music_volume()
            pygame.mixer.music.play(-1)
            if self.music_muted:
                pygame.mixer.music.pause()
            self.current_music = destination
        except (pygame.error, OSError):
            self.current_music = None

    def play(self, name: str, *, cooldown: float = 0.0) -> bool:
        """Play a short effect; unknown or unavailable sounds are harmless."""
        if not self.available or name not in self._sounds:
            return False
        now = time.monotonic()
        if cooldown > 0 and now - self._last_played.get(name, 0.0) < cooldown:
            return False
        try:
            self._channels = [(channel, gain) for channel, gain in self._channels
                              if channel.get_busy()]
            channel = self._sounds[name].play()
            if channel is None:
                return False
            gain = _SOUND_GAINS.get(name, 0.3)
            channel.set_volume(self.volume * gain)
            self._channels.append((channel, gain))
            self._last_played[name] = now
            return True
        except pygame.error:
            return False

    def _apply_music_volume(self) -> None:
        if not self.available:
            return
        try:
            pygame.mixer.music.set_volume(0.0 if self.music_muted else
                                          self.volume * _MUSIC_GAIN)
        except pygame.error:
            pass
