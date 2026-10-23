"""Read-only value field used beside transform sliders and scene metadata."""

import pygame

from .. import fonts, theme


def draw_value(surface, rect, label, value, *, mode="dark", state="default"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    pygame.draw.rect(surface, colors["SURFACE_2"], rect,
                     border_radius=theme.METRICS["radius"])
    border = colors["FOCUS"] if state == "focused" else colors["BORDER"]
    pygame.draw.rect(surface, border, rect, theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    fonts.draw_text(surface, label, (rect.x + theme.SPACE["sm"], rect.centery),
                    "hint", colors["TEXT_MUTED"], anchor="midleft")
    fonts.draw_text(surface, value, (rect.right - theme.SPACE["sm"], rect.centery),
                    "value", colors["TEXT"], anchor="midright",
                    max_width=rect.width // 2)
    return rect
