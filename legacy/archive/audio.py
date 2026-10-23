"""Procedural sound effect and ambient drone synthesis via pygame.mixer.

All audio waveforms are synthesized at runtime using pure Python mathematical functions
(sine waves, frequency sweeps, noise) packed into 16-bit PCM byte arrays.
Zero external audio files required.
"""
from array import array
from math import sin, pi, exp
import os
import random
from typing import Optional, Sequence

import pygame


class AudioSystem:
    """Manages procedural audio synthesis, volume levels, and playback."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.enabled = False
        self.master_volume = 0.8
        self.sfx_volume = 0.8
        self.ambient_volume = 0.4

        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._ambient_channel: Optional[pygame.mixer.Channel] = None
        self._ambient_sound: Optional[pygame.mixer.Sound] = None

        if os.environ.get("RENDERX_NO_AUDIO") == "1":
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=1024)
            self.enabled = True
            self._synthesize_all()
        except (pygame.error, Exception):
            # Graceful fallback: audio device unavailable (e.g. headless CI)
            self.enabled = False

    def _create_pcm_sound(self, samples: Sequence[float]) -> Optional[pygame.mixer.Sound]:
        """Convert float samples in [-1.0, 1.0] to a 16-bit signed mono pygame.mixer.Sound."""
        if not self.enabled:
            return None
        raw_buffer = array("h")
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            raw_buffer.append(int(clamped * 32767))
        try:
            return pygame.mixer.Sound(buffer=raw_buffer)
        except (pygame.error, Exception):
            return None

    def _synthesize_all(self) -> None:
        if not self.enabled:
            return

        # 1. Pulse pistol: rapid downward frequency sweep (880 Hz -> 220 Hz)
        n_pulse = int(self.sample_rate * 0.12)
        samples_pulse = []
        phase = 0.0
        for i in range(n_pulse):
            t = i / self.sample_rate
            progress = i / n_pulse
            freq = 880.0 * (1.0 - progress * 0.75)
            phase += 2 * pi * freq / self.sample_rate
            envelope = exp(-progress * 6.0)
            samples_pulse.append(sin(phase) * envelope)
        sound = self._create_pcm_sound(samples_pulse)
        if sound:
            self._sounds["pulse"] = sound

        # 2. Scatter burst: punchy noise burst with low-mid frequencies
        n_scatter = int(self.sample_rate * 0.2)
        samples_scatter = []
        phase = 0.0
        for i in range(n_scatter):
            progress = i / n_scatter
            freq = 320.0 * (1.0 - progress * 0.5)
            phase += 2 * pi * freq / self.sample_rate
            noise = (random.random() * 2.0 - 1.0) * 0.5
            envelope = exp(-progress * 7.0)
            samples_scatter.append((sin(phase) * 0.6 + noise * 0.4) * envelope)
        sound = self._create_pcm_sound(samples_scatter)
        if sound:
            self._sounds["scatter"] = sound

        # 3. Explosion / Arc blast: low rumble with decaying noise
        n_boom = int(self.sample_rate * 0.45)
        samples_boom = []
        phase = 0.0
        for i in range(n_boom):
            progress = i / n_boom
            freq = 110.0 * (1.0 - progress * 0.6)
            phase += 2 * pi * freq / self.sample_rate
            noise = (random.random() * 2.0 - 1.0) * 0.7
            envelope = (1.0 - progress) * exp(-progress * 3.5)
            samples_boom.append((sin(phase) * 0.4 + noise * 0.6) * envelope)
        sound = self._create_pcm_sound(samples_boom)
        if sound:
            self._sounds["explosion"] = sound

        # 4. Hit sound: short high-contrast tick
        n_hit = int(self.sample_rate * 0.06)
        samples_hit = []
        phase = 0.0
        for i in range(n_hit):
            progress = i / n_hit
            phase += 2 * pi * 440.0 / self.sample_rate
            samples_hit.append(sin(phase) * (1.0 - progress))
        sound = self._create_pcm_sound(samples_hit)
        if sound:
            self._sounds["hit"] = sound

        # 5. Pickup chime: ascending two-tone chime (523 Hz -> 659 Hz)
        n_chime = int(self.sample_rate * 0.22)
        samples_chime = []
        phase = 0.0
        for i in range(n_chime):
            progress = i / n_chime
            freq = 523.25 if progress < 0.5 else 659.25
            phase += 2 * pi * freq / self.sample_rate
            envelope = exp(-((progress % 0.5) / 0.5) * 4.0)
            samples_chime.append(sin(phase) * envelope * 0.8)
        sound = self._create_pcm_sound(samples_chime)
        if sound:
            self._sounds["pickup"] = sound

        # 6. Footstep: very short low thud
        n_step = int(self.sample_rate * 0.04)
        samples_step = []
        phase = 0.0
        for i in range(n_step):
            progress = i / n_step
            phase += 2 * pi * 90.0 / self.sample_rate
            samples_step.append(sin(phase) * (1.0 - progress) * 0.5)
        sound = self._create_pcm_sound(samples_step)
        if sound:
            self._sounds["step"] = sound

        # 7. Ambient dungeon drone (seamless 2.0s loop, 55 Hz base + 110 Hz overtone)
        n_amb = int(self.sample_rate * 2.0)
        samples_amb = []
        for i in range(n_amb):
            t = i / self.sample_rate
            wave1 = sin(2 * pi * 55.0 * t) * 0.4
            wave2 = sin(2 * pi * 110.0 * t + sin(2 * pi * 0.5 * t) * 0.5) * 0.2
            samples_amb.append(wave1 + wave2)
        sound = self._create_pcm_sound(samples_amb)
        if sound:
            self._ambient_sound = sound

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self._sounds.get(name)
        if sound:
            vol = max(0.0, min(1.0, self.master_volume * self.sfx_volume))
            sound.set_volume(vol)
            sound.play()

    def start_ambient(self) -> None:
        if not self.enabled or self._ambient_sound is None:
            return
        if self._ambient_channel is None:
            self._ambient_channel = pygame.mixer.find_channel()
        if self._ambient_channel:
            vol = max(0.0, min(1.0, self.master_volume * self.ambient_volume))
            self._ambient_sound.set_volume(vol)
            self._ambient_channel.play(self._ambient_sound, loops=-1)

    def stop_ambient(self) -> None:
        if self._ambient_channel:
            self._ambient_channel.stop()

    def set_volumes(self, master: float, sfx: float, ambient: float) -> None:
        self.master_volume = max(0.0, min(1.0, master))
        self.sfx_volume = max(0.0, min(1.0, sfx))
        self.ambient_volume = max(0.0, min(1.0, ambient))
        if self._ambient_channel and self._ambient_sound:
            self._ambient_sound.set_volume(self.master_volume * self.ambient_volume)


# Global singleton instance
audio = AudioSystem()
