"""Stateful-looking button rendering shared by panels and the toolbar."""

import pygame

from .. import fonts, icons, theme


def icon_button_rect(rect, label, icon, *, align="center"):
    """Return the shared safe icon placement for a real button rectangle.

    Center-aligned icon buttons use a centered mark when the label cannot fit.
    Wider buttons center the icon and label as one group; left-aligned buttons
    retain a consistent leading inset.
    """
    rect = pygame.Rect(rect)
    size = min(theme.METRICS["icon_medium"] if icon.startswith("shape:")
               else theme.METRICS["icon_small"], max(1, rect.height - 8))
    size = max(1, size)
    padding = theme.SPACE["md"]
    gap = theme.SPACE["sm"]
    label_width = fonts.font("control").size(str(label))[0]
    group_width = size + gap + label_width
    can_fit_group = group_width <= rect.width - padding * 2
    if align == "center" and can_fit_group:
        left = rect.centerx - group_width // 2
    elif align == "center" or not can_fit_group:
        left = rect.centerx - size // 2
    else:
        left = rect.x + padding
    return pygame.Rect(left, rect.centery - size // 2, size, size)


def draw_button(surface, rect, label, *, state="default", mode="dark",
                shortcut=None, icon=None, align="center", transition=1.0):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    base_fill = colors["SURFACE_2"]
    target_fill = theme.component_color(state, mode)
    if state == "default":
        target_fill = colors["SURFACE_1"]
    amount = max(0.0, min(1.0, transition))
    fill = tuple(round(a + (b - a) * amount)
                 for a, b in zip(base_fill, target_fill))
    pygame.draw.rect(surface, fill, rect, border_radius=theme.METRICS["radius"])
    border = colors["FOCUS"] if state == "focused" else colors["BORDER"]
    pygame.draw.rect(surface, border, rect, theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    if state == "active":
        label_color = colors["ACCENT_TEXT"]
    elif state == "disabled":
        label_color = colors["TEXT_DIM"]
    else:
        label_color = colors["TEXT"]
    content = rect.inflate(-theme.SPACE["md"] * 2, 0)
    content.width = max(0, content.width)
    if icon:
        icon_rect = icon_button_rect(rect, label, icon, align=align)
        icons.draw_icon(surface, icon, icon_rect, label_color)
        if align == "center" and icon_rect.centerx == rect.centerx:
            content.width = 0
        else:
            content.x = icon_rect.right + theme.SPACE["sm"]
    if shortcut:
        hint_width = fonts.font("micro").size(shortcut)[0]
        fonts.draw_text(surface, shortcut, (rect.right - theme.SPACE["sm"], rect.centery),
                        "micro", colors["TEXT_MUTED"], anchor="midright")
        content.width = max(0, rect.right - theme.SPACE["lg"] - hint_width - content.x)
    elif content.width > 0:
        content.width = max(0, rect.right - theme.SPACE["md"] - content.x)
    if content.width > 0:
        anchor = "midleft" if align == "left" or icon else "center"
        position = ((content.x, rect.centery) if anchor == "midleft"
                    else (content.centerx, rect.centery))
        fonts.draw_text(surface, label, position, "control", label_color,
                        anchor=anchor, max_width=content.width)
    return rect
