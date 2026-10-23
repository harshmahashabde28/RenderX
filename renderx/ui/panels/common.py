"""Shared drawing helpers used by dock panels."""

import pygame

from .. import fonts, theme
from ..components import draw_button, draw_section


def draw_panel(surface, rect, mode="dark"):
    colors = theme.palette(mode)
    pygame.draw.rect(surface, colors["SURFACE_1"], rect)
    pygame.draw.line(surface, colors["BORDER"], rect.topleft,
                     (rect.x, rect.bottom), theme.METRICS["border"])


def title(surface, rect, text, mode="dark"):
    colors = theme.palette(mode)
    fonts.draw_text(surface, text, (rect.x, rect.y), "hint", colors["TEXT_MUTED"],
                    bold=True, max_width=rect.width)


def section(surface, rect, text, ui, action, *, expanded=True, mode="dark"):
    draw_section(surface, rect, text, mode=mode, expanded=expanded)
    ui.button(action, text, rect)


def control(surface, rect, text, ui, action, *, mode="dark", state="default",
            shortcut=None, icon=None, align="left"):
    ui.button(action, text, rect, active=state == "active")
    ui.paint_button(surface, action, mode=mode, state=state,
                    shortcut=shortcut, icon=icon, align=align)
