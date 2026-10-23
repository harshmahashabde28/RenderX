"""Compact technical status strip with tabular data and a contextual hint."""

import pygame

from .. import fonts, theme


def draw_status(surface, rect, items, hint="", *, mode="dark"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    pygame.draw.rect(surface, colors["SURFACE_1"], rect)
    pygame.draw.line(surface, colors["BORDER"], rect.topleft, rect.topright,
                     theme.METRICS["border"])
    x = rect.x + theme.SPACE["lg"]
    for label, value in items:
        text = f"{label}  {value}"
        image = fonts.font("status").render(text, True, colors["TEXT_MUTED"])
        surface.blit(image, image.get_rect(midleft=(x, rect.centery)))
        x += image.get_width() + theme.SPACE["xl"]
    if hint:
        fonts.draw_text(surface, hint, (rect.right - theme.SPACE["lg"], rect.centery),
                        "hint", colors["TEXT_DIM"], anchor="midright",
                        max_width=max(0, rect.right - theme.SPACE["lg"] - x))
    return rect
