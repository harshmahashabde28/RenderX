"""One-pixel dock separators with a clear resize hit target."""

import pygame

from .. import theme


def draw_splitter(surface, rect, *, mode="dark", hover=False):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    line_color = colors["ACCENT"] if hover else colors["BORDER"]
    center = rect.centerx if rect.width >= rect.height else rect.centery
    if rect.width >= rect.height:
        pygame.draw.line(surface, line_color, (center, rect.y), (center, rect.bottom),
                         theme.METRICS["border"])
    else:
        pygame.draw.line(surface, line_color, (rect.x, center), (rect.right, center),
                         theme.METRICS["border"])
    return rect
