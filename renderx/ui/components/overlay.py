"""Plain bordered dialog for shortcuts and confirmation information."""

import pygame

from .. import fonts, theme
from .button import draw_button


def draw_overlay(surface, title, rows, *, mode="dark", footer_action=None,
                 footer_actions=None, wide=True,
                 hint="Press Esc or F1 to close"):
    colors = theme.palette(mode)
    veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    veil.fill((*colors["CANVAS"], 190))
    surface.blit(veil, (0, 0))
    padding = theme.SPACE["xxl"]
    # Shortcut rows have a longer right-hand column than small preference
    # dialogs. Keep the help panel wide enough to show the live bindings.
    preferred_width = (max(theme.METRICS["dialog_width"], 920) if wide else
                       theme.METRICS["dialog_width"])
    width = min(preferred_width,
                surface.get_width() - padding * 2)
    actions = (tuple(footer_actions) if footer_actions is not None else
               ((footer_action,) if footer_action else ()))
    action_height = (theme.METRICS["control_height"] + theme.SPACE["sm"]
                     if actions else 0)
    available_height = (surface.get_height() - padding * 2 -
                        theme.METRICS["title_height"] - action_height)
    row_height = min(theme.METRICS["row_height"],
                     max(18, available_height // max(1, len(rows))))
    height = (padding * 2 + theme.METRICS["title_height"] +
              len(rows) * row_height + action_height)
    panel = pygame.Rect(0, 0, width, height)
    panel.center = surface.get_rect().center
    pygame.draw.rect(surface, colors["SURFACE_1"], panel,
                     border_radius=theme.METRICS["radius"])
    pygame.draw.rect(surface, colors["BORDER"], panel, theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    fonts.draw_text(surface, title, (panel.x + padding, panel.y + padding),
                    "section", colors["TEXT"], bold=True)
    y = panel.y + padding + theme.METRICS["title_height"]
    for label, key in rows:
        fonts.draw_text(surface, label, (panel.x + padding, y),
                        "control", colors["TEXT"],
                        max_width=panel.width // 2 - padding)
        fonts.draw_text(surface, key, (panel.right - padding, y),
                        "value", colors["TEXT_MUTED"], anchor="topright",
                        max_width=panel.width // 2 - padding)
        y += row_height
    action_rects = {}
    if actions:
        gap = theme.SPACE["sm"]
        button_width = ((panel.width - padding * 2 - gap * (len(actions) - 1)) //
                        len(actions))
        for index, label in enumerate(actions):
            action_rect = pygame.Rect(
                panel.x + padding + index * (button_width + gap),
                panel.bottom - padding - theme.METRICS["control_height"],
                button_width, theme.METRICS["control_height"])
            draw_button(surface, action_rect, label, mode=mode, align="left")
            action_rects[label] = action_rect
    fonts.draw_text(surface, hint,
                    (panel.centerx, panel.bottom - padding // 2), "hint",
                    colors["TEXT_MUTED"], anchor="center")
    if footer_actions is not None:
        return panel, action_rects
    return (panel, action_rects.get(footer_action)) if footer_action else panel
