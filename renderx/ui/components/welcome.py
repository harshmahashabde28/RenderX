"""First-run orientation for the 3D workspace and file controls."""

import pygame

from .. import fonts, theme
from renderx.input_map import modifier_name
from .button import draw_button


def draw_welcome(surface, preset, *, mode="dark"):
    colors = theme.palette(mode)
    veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    veil.fill((*colors["CANVAS"], 190))
    surface.blit(veil, (0, 0))
    padding = theme.SPACE["xxl"]
    width = min(theme.METRICS["dialog_width"], surface.get_width() - padding * 2)
    height = padding * 2 + theme.METRICS["title_height"] + 3 * theme.METRICS["row_height"]
    panel = pygame.Rect(0, 0, width, height)
    panel.center = surface.get_rect().center
    pygame.draw.rect(surface, colors["SURFACE_1"], panel,
                     border_radius=theme.METRICS["radius"])
    pygame.draw.rect(surface, colors["BORDER"], panel, theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    fonts.draw_text(surface, "Welcome to RenderX",
                    (panel.x + padding, panel.y + padding), "section",
                    colors["TEXT"], bold=True)
    modifier = modifier_name()
    lines = (
        f"Open an OBJ with {modifier}+O, or choose a sample in the Scene panel.",
        ("{}: left-drag orbits, right or middle-drag pans, and the wheel zooms."
         .format(preset)),
        f"Use F1 for shortcuts. Preferences are under {modifier}+,.",
    )
    y = panel.y + padding + theme.METRICS["title_height"]
    for line in lines:
        fonts.draw_wrapped(surface, line, (panel.x + padding, y),
                           panel.width - padding * 2, "hint", colors["TEXT"])
        y += theme.METRICS["row_height"]
    button_height = theme.METRICS["control_height"]
    gap = theme.SPACE["sm"]
    button_width = (panel.width - 2 * padding - gap) // 2
    buttons = {}
    for index, (key, label) in enumerate((
            ("explore", "Explore workspace"),
            ("continue", "Continue to Breakpoint"))):
        rect = pygame.Rect(panel.x + padding + index * (button_width + gap),
                           panel.bottom - padding - button_height,
                           button_width, button_height)
        draw_button(surface, rect, label, mode=mode,
                    state="active" if key == "explore" else "default")
        buttons[key] = rect
    return panel, buttons
