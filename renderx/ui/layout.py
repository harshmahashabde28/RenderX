"""Responsive dock and toolbar geometry, independent from renderer math."""

from dataclasses import dataclass

import pygame

from . import theme
from .fonts import font


DESTINATION_LABELS = {
    "Explore": "Explore",
    "Challenges": "Challenge",
    "Maze": "Maze",
    "Shooter": "Shooter",
}


@dataclass(frozen=True)
class AppLayout:
    width: int
    height: int
    topbar: pygame.Rect
    statusbar: pygame.Rect
    left_dock: pygame.Rect
    left_splitter: pygame.Rect
    viewport_frame: pygame.Rect
    viewport: pygame.Rect
    right_splitter: pygame.Rect
    right_dock: pygame.Rect
    brand: pygame.Rect
    navigation: dict[str, pygame.Rect]
    projection: pygame.Rect
    render_mode: pygame.Rect
    import_obj: pygame.Rect
    screenshot: pygame.Rect
    theme_toggle: pygame.Rect
    help_button: pygame.Rect
    music_toggle: pygame.Rect
    audio_slider: pygame.Rect


def build_layout(size, left_width=None, right_width=None,
                 left_collapsed=False, right_collapsed=False) -> AppLayout:
    """Fit docks, viewport, status strip, and toolbar into the live canvas."""
    width, height = max(1, int(size[0])), max(1, int(size[1]))
    metrics, space = theme.METRICS, theme.SPACE
    top_h, status_h, splitter = metrics["topbar_height"], metrics["status_height"], metrics["splitter"]
    body_y = top_h
    body_h = max(1, height - top_h - status_h)
    left_default = left_width or metrics["left_dock"]
    right_default = right_width or metrics["right_dock"]
    left_min = metrics["collapsed_rail"] if left_collapsed else metrics["dock_min"]
    right_min = metrics["collapsed_rail"] if right_collapsed else metrics["dock_min"]
    left_max = metrics["collapsed_rail"] if left_collapsed else metrics["dock_max"]
    right_max = metrics["collapsed_rail"] if right_collapsed else metrics["dock_max"]
    max_docks = max(0, width - splitter * 2 - metrics["min_viewport_width"])
    left_width = max(left_min, min(left_max, int(left_default)))
    right_width = max(right_min, min(right_max, int(right_default)))
    if left_width + right_width > max_docks:
        excess = left_width + right_width - max_docks
        left_cut = min(excess // 2 + excess % 2, left_width - left_min)
        left_width -= left_cut
        right_width = max(right_min, right_width - (excess - left_cut))

    left = pygame.Rect(0, body_y, left_width, body_h)
    left_split = pygame.Rect(left.right, body_y, splitter, body_h)
    right = pygame.Rect(width - right_width, body_y, right_width, body_h)
    right_split = pygame.Rect(right.x - splitter, body_y, splitter, body_h)
    center_left, center_right = left_split.right, right_split.x
    viewport_frame = pygame.Rect(center_left, body_y, max(1, center_right - center_left), body_h)
    inset = space["md"]
    viewport = viewport_frame.inflate(-inset * 2, -inset * 2)
    if viewport.width < 1 or viewport.height < 1:
        viewport = viewport_frame.copy()

    brand = pygame.Rect(space["lg"], space["sm"], metrics["brand_width"], top_h - space["sm"] * 2)
    nav_x = brand.right + space["lg"]
    destinations = tuple(DESTINATION_LABELS)
    compact = width < 760
    labels = {name: (DESTINATION_LABELS[name][:5] if compact
                     else DESTINATION_LABELS[name]) for name in destinations}
    nav_total = sum(font("control").size(labels[name])[0] + space["md"] * 2
                    for name in destinations) + space["xs"] * (len(destinations) - 1)
    nav = _segments(nav_x, space["sm"], top_h - space["sm"] * 2,
                    destinations, labels)
    nav_total = max((rect.right for rect in nav.values()), default=nav_x) - nav_x
    x = nav_x + nav_total + space["md"]
    projection = pygame.Rect(x, space["sm"], metrics["projection_width"], top_h - space["sm"] * 2)
    x = projection.right + space["sm"]
    render_mode = pygame.Rect(x, space["sm"], metrics["render_mode_width"], top_h - space["sm"] * 2)
    x = render_mode.right + space["md"]
    icon_width = metrics["hit_target"]
    help_button = pygame.Rect(width - space["lg"] - icon_width,
                              space["sm"], icon_width, top_h - space["sm"] * 2)
    theme_toggle = help_button.move(-icon_width - space["xs"], 0)
    screenshot = theme_toggle.move(-icon_width - space["xs"], 0)
    import_obj = screenshot.move(-icon_width - space["xs"], 0)
    music_toggle = import_obj.move(-icon_width - space["xs"], 0)
    audio_right = music_toggle.x - space["xs"]
    audio_left = render_mode.right + space["md"]
    audio_width = max(1, min(124, audio_right - audio_left))
    audio_slider = pygame.Rect(audio_right - audio_width, space["sm"],
                               audio_width, top_h - space["sm"] * 2)
    status = pygame.Rect(0, height - status_h, width, status_h)
    return AppLayout(width, height, pygame.Rect(0, 0, width, top_h), status,
                     left, left_split, viewport_frame, viewport, right_split,
                     right, brand, nav, projection, render_mode, import_obj,
                     screenshot, theme_toggle, help_button, music_toggle,
                     audio_slider)


def _segments(x, y, height, names, labels):
    gap = theme.SPACE["xs"]
    result = {}
    for name in names:
        item_width = max(1, font("control").size(labels[name])[0] +
                         theme.SPACE["md"] * 2)
        result[name] = pygame.Rect(x, y, item_width, height)
        x += item_width + gap
    return result
