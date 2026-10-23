"""Small pointer-anchored menus for familiar viewport and object actions."""

import pygame

from .. import theme
from .button import draw_button


def draw_context_menu(surface, position, items, *, mode="dark", hovered=None,
                      focused=None):
    """Draw labeled context actions and keep the popup inside the canvas."""
    colors = theme.palette(mode)
    padding = theme.SPACE["xs"]
    row_height = theme.METRICS["control_height"] + theme.SPACE["xs"]
    width = min(280, max(180, surface.get_width() - padding * 2))
    height = padding * 2 + row_height * len(items)
    panel = pygame.Rect(position[0], position[1], width, height)
    panel.clamp_ip(surface.get_rect())
    pygame.draw.rect(surface, colors["SURFACE_1"], panel,
                     border_radius=theme.METRICS["radius"])
    pygame.draw.rect(surface, colors["BORDER"], panel,
                     theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    actions = {}
    y = panel.y + padding
    for action, label in items:
        rect = pygame.Rect(panel.x + padding, y, panel.width - padding * 2,
                           row_height)
        state = ("hover" if action == hovered else
                 "focused" if action == focused else "default")
        draw_button(surface, rect, label, mode=mode, state=state, align="left")
        actions[action] = rect
        y += row_height
    return panel, actions
