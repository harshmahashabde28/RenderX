"""Restrained first-run landing screen for the RenderX desktop app."""

import pygame

from . import fonts, theme
from .components.button import draw_button


_ACTIONS = (
    ("open_obj", "Open OBJ…"),
    ("shortcuts", "Shortcuts"),
    ("about", "About"),
)


def draw_landing(surface, logo, *, mode="dark", version_text="",
                 hover=None, pressed=None, focused=None):
    """Draw the launch page and return its live hit rectangles."""
    colors = theme.palette(mode)
    surface.fill(colors["CANVAS"])

    logo_height = min(250, round(surface.get_height() * .22),
                      max(100, round(surface.get_width() * .13)))
    mark_height = round(logo_height * .94)
    description_height = fonts.font("body").get_linesize()
    body_height = description_height + 20 + 36 + 12 + 32
    clear_space = mark_height
    total_height = logo_height + clear_space + body_height
    footer_clearance = 40
    top = max(clear_space,
              (surface.get_height() - total_height - footer_clearance) // 2)

    logo_rect = logo.get_rect(midtop=(surface.get_width() // 2, top))
    plate = logo_rect.inflate(16, 16)
    plate_color = theme.palette("dark")
    pygame.draw.rect(surface, plate_color["VIEWPORT"], plate,
                     border_radius=theme.METRICS["radius"])
    pygame.draw.rect(surface, plate_color["BORDER"], plate,
                     theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    surface.blit(logo, logo_rect)

    description = "3D wireframe rendering engine, built from scratch in Python."
    desc_y = logo_rect.bottom + clear_space
    fonts.draw_text(surface, description,
                    (surface.get_width() // 2, desc_y), "body",
                    colors["TEXT_MUTED"], anchor="midtop",
                    max_width=surface.get_width() - theme.SPACE["xxl"] * 2)

    actions = {}
    primary = pygame.Rect(0, 0, 188, 36)
    primary.midtop = (surface.get_width() // 2,
                      desc_y + description_height + 20)
    actions[("landing", "explore")] = primary
    primary_hover = hover == ("landing", "explore")
    primary_pressed = pressed == ("landing", "explore")
    _button(surface, primary, "Open Explorer", "active",
            focused == ("landing", "explore"), mode)
    if primary_hover:
        pygame.draw.rect(surface, colors["FOCUS"], primary, 1,
                         border_radius=theme.METRICS["radius"])
    if primary_pressed:
        pressed_layer = pygame.Surface(primary.size, pygame.SRCALPHA)
        pressed_layer.fill((*colors["TEXT"], 30))
        surface.blit(pressed_layer, primary.topleft)

    secondary_y = primary.bottom + 12
    secondary_gap = theme.SPACE["sm"]
    secondary_width = 126
    secondary_total = secondary_width * len(_ACTIONS) + secondary_gap * (len(_ACTIONS) - 1)
    secondary_x = (surface.get_width() - secondary_total) // 2
    for index, (name, label) in enumerate(_ACTIONS):
        action = ("landing", name)
        rect = pygame.Rect(secondary_x + index * (secondary_width + secondary_gap),
                           secondary_y, secondary_width, 32)
        actions[action] = rect
        _button(surface, rect, label,
                "pressed" if pressed == action else
                "hover" if hover == action else "default",
                focused == action, mode)

    fonts.draw_text(surface, version_text,
                    (surface.get_width() // 2,
                     surface.get_height() - theme.SPACE["lg"]),
                    "status", colors["TEXT_DIM"], anchor="midbottom")
    return actions


def _button(surface, rect, label, state, focused, mode):
    """Share the application's button states and add an explicit focus ring."""
    draw_button(surface, rect, label, mode=mode, state=state, align="center")
    if focused:
        _focus_ring(surface, rect.inflate(4, 4), theme.palette(mode)["FOCUS"])


def _focus_ring(surface, rect, color):
    pygame.draw.rect(surface, color, rect, 1,
                     border_radius=theme.METRICS["radius"] + 1)
