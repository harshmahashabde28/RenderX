"""Compact preferences dialog for interaction settings."""

import pygame

from .. import fonts, theme
from .button import draw_button


def draw_preferences(surface, current, *, mode="dark"):
    colors = theme.palette(mode)
    veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    veil.fill((*colors["CANVAS"], 190))
    surface.blit(veil, (0, 0))
    padding = theme.SPACE["xxl"]
    row_height = theme.METRICS["row_height"]
    width = min(theme.METRICS["dialog_width"], surface.get_width() - padding * 2)
    height = padding * 2 + theme.METRICS["title_height"] + 3 * row_height
    panel = pygame.Rect(0, 0, width, height)
    panel.center = surface.get_rect().center
    pygame.draw.rect(surface, colors["SURFACE_1"], panel,
                     border_radius=theme.METRICS["radius"])
    pygame.draw.rect(surface, colors["BORDER"], panel, theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    fonts.draw_text(surface, "Preferences", (panel.x + padding, panel.y + padding),
                    "section", colors["TEXT"], bold=True)
    y = panel.y + padding + theme.METRICS["title_height"]
    fonts.draw_text(surface, "Viewport navigation", (panel.x + padding, y),
                    "hint", colors["TEXT_MUTED"])
    y += row_height
    gap = theme.SPACE["sm"]
    button_width = (panel.width - 2 * padding - gap) // 2
    buttons = {}
    for index, (name, label) in enumerate((
            ("Orbit Viewer", "Orbit Viewer"),
            ("RenderX Classic", "RenderX Classic"))):
        rect = pygame.Rect(panel.x + padding + index * (button_width + gap),
                           y, button_width, theme.METRICS["control_height"])
        draw_button(surface, rect, label, mode=mode,
                    state="active" if name == current else "default")
        buttons[name] = rect
    fonts.draw_text(surface, "Settings save automatically",
                    (panel.centerx, panel.bottom - padding // 2), "hint",
                    colors["TEXT_MUTED"], anchor="center")
    return panel, buttons
