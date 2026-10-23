"""Locally bundled, cached UI fonts and text layout helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

from . import theme


FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
FONT_FILES = {
    "ui": FONT_DIR / "Inter-Variable.ttf",
    "mono": FONT_DIR / "IBM-Plex-Mono-Regular.ttf",
}


@lru_cache(maxsize=48)
def font(role: str, size: int | None = None, bold: bool = False) -> pygame.font.Font:
    """Get a cached font for a named type role; never resolve system fonts."""
    family, role_size = theme.TYPE_SCALE.get(role, theme.TYPE_SCALE["body"])
    path = FONT_FILES[family]
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        result = pygame.font.Font(str(path), role_size if size is None else size)
    except (OSError, pygame.error):
        result = pygame.font.Font(None, role_size if size is None else size)
    result.set_bold(bool(bold))
    return result


@lru_cache(maxsize=4096)
def _render(role: str, text: str, color: tuple[int, int, int], bold: bool) -> pygame.Surface:
    return font(role, bold=bold).render(text, True, color)


def draw_text(surface: pygame.Surface, value: object, position: tuple[int, int],
              role: str = "body", color: tuple[int, int, int] | None = None,
              *, anchor: str = "topleft", bold: bool = False,
              max_width: int | None = None) -> pygame.Rect:
    """Draw cached anti-aliased text with stable anchors and safe truncation."""
    color = color or theme.palette()["TEXT"]
    text = str(value)
    typeface = font(role, bold=bold)
    if max_width is not None and typeface.size(text)[0] > max_width:
        suffix = "..."
        if typeface.size(suffix)[0] > max_width:
            text = ""
        else:
            while text and typeface.size(text + suffix)[0] > max_width:
                text = text[:-1]
            text = text.rstrip() + suffix
    if typeface.size(text)[0] <= 240:
        image = _render(role, text, color, bold)
    else:
        image = typeface.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, position)
    surface.blit(image, rect)
    return rect


def draw_wrapped(surface: pygame.Surface, value: object, position: tuple[int, int],
                 width: int, role: str = "body",
                 color: tuple[int, int, int] | None = None,
                 *, line_gap: int | None = None) -> int:
    """Wrap a short panel paragraph and return its last baseline position."""
    typeface = font(role)
    colors = color or theme.palette()["TEXT"]
    max_width = max(1, int(width))
    words, rows, row = str(value).split(), [], ""
    for word in words:
        candidate = word if not row else row + " " + word
        if typeface.size(candidate)[0] <= max_width or not row:
            row = candidate
        else:
            rows.append(row)
            row = word
    if row:
        rows.append(row)
    gap = theme.SPACE["xs"] if line_gap is None else line_gap
    y = position[1]
    for text in rows:
        image = _render(role, text, colors, False)
        surface.blit(image, (position[0], y))
        y += max(typeface.get_linesize(), image.get_height()) + gap
    return y


def clear_cache() -> None:
    """Release rendered glyph surfaces before the Pygame app shuts down."""
    font.cache_clear()
    _render.cache_clear()
