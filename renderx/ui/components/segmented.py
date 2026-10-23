"""Small mutually exclusive choice control for projection and render modes."""

import pygame

from .. import fonts, theme


def draw_segmented(surface, rect, options, selected, *, mode="dark", state="default"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    gap = theme.SPACE["xs"]
    item_width = max(1, (rect.width - gap * max(0, len(options) - 1)) // max(1, len(options)))
    hitboxes = {}
    for index, option in enumerate(options):
        item = pygame.Rect(rect.x + index * (item_width + gap), rect.y,
                           item_width, rect.height)
        active = option == selected
        fill = colors["ACCENT"] if active else colors["SURFACE_2"]
        pygame.draw.rect(surface, fill, item, border_radius=theme.METRICS["radius"])
        pygame.draw.rect(surface, colors["BORDER"], item, theme.METRICS["border"],
                         border_radius=theme.METRICS["radius"])
        text_color = colors["ACCENT_TEXT"] if active else colors["TEXT"]
        fonts.draw_text(surface, option, item.center, "control", text_color,
                        anchor="center", max_width=item.width - theme.SPACE["sm"])
        hitboxes[option] = item
    return hitboxes
