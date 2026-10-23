"""Dock-panel section header with a compact collapse affordance."""

import pygame

from .. import fonts, icons, theme


def draw_section(surface, rect, label, *, mode="dark", expanded=True,
                 count=None, state="default"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    pygame.draw.line(surface, colors["BORDER"], (rect.x, rect.bottom),
                     (rect.right, rect.bottom), theme.METRICS["border"])
    glyph = "expand" if expanded else "chevron"
    size = theme.METRICS["icon_small"]
    icons.draw_icon(surface, glyph,
                    pygame.Rect(rect.x, rect.centery - size // 2, size, size),
                    colors["TEXT_MUTED"])
    text = label if count is None else f"{label}  {count}"
    fonts.draw_text(surface, text, (rect.x + size + theme.SPACE["sm"], rect.centery),
                    "hint", colors["TEXT"], anchor="midleft")
    return rect
