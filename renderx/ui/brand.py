"""Load and cache the supplied RenderX identity artwork at display sizes."""

from functools import lru_cache
from pathlib import Path

import pygame


_LOGO_DIRECTORY = Path(__file__).resolve().parents[2] / "assets" / "logo"


@lru_cache(maxsize=2)
def _source(name: str) -> pygame.Surface:
    """Keep the original high-resolution transparent artwork in memory."""
    return pygame.image.load(str(_LOGO_DIRECTORY / name))


@lru_cache(maxsize=48)
def _scaled(name: str, size: tuple[int, int]) -> pygame.Surface:
    """Downsample one source once per requested target size."""
    return pygame.transform.smoothscale(_source(name), size)


def wordmark(max_width: int, max_height: int) -> pygame.Surface:
    """Return a cached wordmark that fits its box without changing its ratio."""
    source = _source("renderx-logo.png")
    scale = min(max(1, max_width) / source.get_width(),
                max(1, max_height) / source.get_height())
    size = (max(1, round(source.get_width() * scale)),
            max(1, round(source.get_height() * scale)))
    return _scaled("renderx-logo.png", size)


def mark(side: int) -> pygame.Surface:
    """Return the square supplied mark at one cached, antialiased size."""
    size = max(1, int(side))
    return _scaled("renderx-mark-1024.png", (size, size))


def clear_cache() -> None:
    """Release scaled UI images when the display shuts down."""
    _source.cache_clear()
    _scaled.cache_clear()
