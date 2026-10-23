"""Compact on/off control with a visible active state."""

import pygame

from .. import fonts, theme


def draw_toggle(surface, rect, label, value, *, mode="dark", state="default"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    fonts.draw_text(surface, label, (rect.x, rect.centery), "control",
                    colors["TEXT_DIM"] if state == "disabled" else colors["TEXT"],
                    anchor="midleft", max_width=max(0, rect.width - theme.METRICS["hit_target"] - theme.SPACE["md"]))
    height = theme.METRICS["hit_target"] - theme.SPACE["sm"]
    width = height + theme.SPACE["sm"]
    track = pygame.Rect(rect.right - width, rect.centery - height // 2, width, height)
    fill = colors["ACCENT"] if value else colors["SURFACE_3"]
    pygame.draw.rect(surface, fill, track, border_radius=height // 2)
    knob = height - theme.SPACE["xs"]
    inset = theme.METRICS["border"] * 2
    x = track.right - knob - inset if value else track.x + inset
    pygame.draw.circle(surface, colors["ACCENT_TEXT"] if value else colors["TEXT_MUTED"],
                       (x + knob // 2, track.centery), knob // 2)
    return track
