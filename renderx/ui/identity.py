"""Shared window title and branded icon for RenderX display modes."""

import pygame

from . import brand


def set_window_identity(title: str) -> None:
    """Apply the supplied square mark whenever a Pygame window is created."""
    pygame.display.set_caption(title)
    pygame.display.set_icon(brand.mark(128))
