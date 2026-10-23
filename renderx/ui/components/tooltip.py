"""Compact hover help rendered without shadows or visual effects."""

import pygame

from .. import fonts, theme


def draw_tooltip(surface, position, text, *, mode="dark", max_width=None):
    colors = theme.palette(mode)
    width = max_width or theme.METRICS["tooltip_width"]
    typeface = fonts.font("hint")
    words, lines, line = str(text).split(), [], ""
    for word in words:
        candidate = word if not line else line + " " + word
        if typeface.size(candidate)[0] <= width - theme.SPACE["lg"] or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    line_height = typeface.get_linesize()
    box = pygame.Rect(position[0], position[1], width,
                      line_height * len(lines) + theme.SPACE["md"] * 2)
    bounds = surface.get_rect()
    if box.right > bounds.right:
        box.right = bounds.right - theme.SPACE["xs"]
    if box.bottom > bounds.bottom:
        box.bottom = position[1] - theme.SPACE["xs"]
    pygame.draw.rect(surface, colors["SURFACE_2"], box,
                     border_radius=theme.METRICS["radius"])
    pygame.draw.rect(surface, colors["BORDER"], box,
                     theme.METRICS["border"], border_radius=theme.METRICS["radius"])
    y = box.y + theme.SPACE["sm"]
    for value in lines:
        fonts.draw_text(surface, value, (box.x + theme.SPACE["sm"], y),
                        "hint", colors["TEXT"])
        y += line_height
    return box
