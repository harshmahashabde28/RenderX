"""Clear launch panel for Breakpoint, the separate 3D shooter destination."""

import pygame

from .. import fonts, theme
from .common import draw_panel


def draw_shooter_panel(surface, rect, ui, *, mode="dark"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    draw_panel(surface, rect, mode)
    x = rect.x + theme.SPACE["md"]
    width = max(1, rect.width - theme.SPACE["lg"])
    y = rect.y + theme.SPACE["md"]
    fonts.draw_text(surface, "GAME DETAILS", (x, y), "hint", colors["TEXT_MUTED"], bold=True)
    y += theme.METRICS["section_height"]
    fonts.draw_text(surface, "Field operations", (x, y), "section", colors["TEXT"], bold=True)
    y += theme.METRICS["row_height"]
    fonts.draw_wrapped(surface,
                       "A first-person survival run rendered in a separate 3D arena.",
                       (x, y), width, "hint", colors["TEXT_MUTED"])
    y += theme.METRICS["row_height"] * 2
    for label, value in (("Waves", "Endless"), ("Cover", "Destructible"),
                         ("Movement", "Dash and strafe"), ("Objective", "Survive")):
        fonts.draw_text(surface, label, (x, y), "hint", colors["TEXT_MUTED"])
        fonts.draw_text(surface, value, (rect.right - theme.SPACE["md"], y),
                        "hint", colors["TEXT"], anchor="topright")
        y += theme.METRICS["row_height"]
    fonts.draw_wrapped(surface, "WASD move   ·   Mouse aim   ·   Click fire   ·   Shift dash",
                       (x, y + theme.SPACE["sm"]), width, "micro", colors["TEXT_DIM"])
    button = pygame.Rect(x, rect.bottom - theme.SPACE["lg"] - theme.METRICS["control_height"],
                         width, theme.METRICS["control_height"])
    ui.button(("shooter_launch",), "Choose difficulty", button, active=True)
    ui.paint_button(surface, ("shooter_launch",), mode=mode, state="active",
                    icon="play", align="center")
