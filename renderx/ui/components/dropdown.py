"""A single-line selection control with room for a chevron and shortcut."""

import pygame

from .. import fonts, icons, theme
from .button import draw_button


def draw_dropdown(surface, rect, label, value, *, mode="dark", state="default"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    pygame.draw.rect(surface, theme.component_color(state, mode), rect,
                     border_radius=theme.METRICS["radius"])
    border = colors["FOCUS"] if state == "focused" else colors["BORDER"]
    pygame.draw.rect(surface, border, rect, theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    fonts.draw_text(surface, label, (rect.x + theme.SPACE["sm"], rect.centery),
                    "hint", colors["TEXT_MUTED"], anchor="midleft",
                    max_width=rect.width // 3)
    fonts.draw_text(surface, value, (rect.centerx, rect.centery), "control",
                    colors["TEXT"], anchor="midleft",
                    max_width=max(0, rect.width - theme.METRICS["icon_small"] - theme.SPACE["xl"]))
    size = theme.METRICS["icon_small"]
    icons.draw_icon(surface, "expand",
                    pygame.Rect(rect.right - size - theme.SPACE["sm"],
                                rect.centery - size // 2, size, size),
                    colors["TEXT_MUTED"])
    return rect


def draw_dropdown_options(surface, anchor, options, selected, *, mode="dark",
                          focused=None):
    """Open a keyboard-friendly options list adjacent to its control."""
    colors = theme.palette(mode)
    anchor = pygame.Rect(anchor)
    padding = theme.SPACE["xs"]
    row_height = theme.METRICS["control_height"] + theme.SPACE["xs"]
    width = anchor.width
    height = padding * 2 + row_height * len(options)
    rect = pygame.Rect(anchor.x, anchor.bottom + theme.SPACE["xs"], width, height)
    safe_bounds = surface.get_rect().inflate(-theme.SPACE["xs"] * 2,
                                             -theme.SPACE["xs"] * 2)
    if rect.bottom > safe_bounds.bottom:
        rect.bottom = anchor.top - theme.SPACE["xs"]
    rect.clamp_ip(safe_bounds)
    pygame.draw.rect(surface, colors["SURFACE_1"], rect,
                     border_radius=theme.METRICS["radius"])
    pygame.draw.rect(surface, colors["BORDER"], rect,
                     theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    actions = {}
    y = rect.y + padding
    for option in options:
        item = pygame.Rect(rect.x + padding, y, rect.width - padding * 2,
                           row_height)
        state = ("active" if option == selected else
                 "focused" if option == focused else "default")
        draw_button(surface, item, option, mode=mode, state=state, align="left")
        actions[option] = item
        y += row_height
    return rect, actions
