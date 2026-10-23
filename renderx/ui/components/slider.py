"""A compact range control with an aligned numeric readout."""

import pygame

from .. import fonts, theme


def draw_slider(surface, rect, label, value, low, high, *, mode="dark",
                state="default", value_text=None):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    fonts.draw_text(surface, label, (rect.x, rect.y), "control", colors["TEXT"],
                    max_width=rect.width // 2)
    value_text = value_text if value_text is not None else f"{value:.2f}"
    fonts.draw_text(surface, value_text, (rect.right, rect.y), "value",
                    colors["TEXT_MUTED"], anchor="topright")
    bar_y = rect.y + theme.METRICS["row_height"] - theme.SPACE["sm"]
    bar = pygame.Rect(rect.x, bar_y, rect.width, theme.METRICS["border"] * 2)
    pygame.draw.rect(surface, colors["SURFACE_4"], bar)
    ratio = 0.0 if high <= low else max(0.0, min(1.0, (value - low) / (high - low)))
    fill = bar.copy()
    fill.width = round(bar.width * ratio)
    pygame.draw.rect(surface, colors["ACCENT"], fill)
    radius = theme.SPACE["sm"] // 2
    pygame.draw.circle(surface, colors["ACCENT"], (bar.x + fill.width, bar.centery), radius)
    if state == "focused":
        pygame.draw.rect(surface, colors["FOCUS"], rect.inflate(theme.SPACE["xs"], theme.SPACE["xs"]),
                         theme.METRICS["border"], border_radius=theme.METRICS["radius"])
    return pygame.Rect(rect.x, bar_y - theme.SPACE["sm"], rect.width,
                       theme.METRICS["hit_target"])


def slider_value(position, rect, low, high):
    rect = pygame.Rect(rect)
    ratio = 0 if rect.width <= 0 else max(0, min(1, (position[0] - rect.x) / rect.width))
    return low + (high - low) * ratio
