"""Crisp SVG controls and small wireframe previews rendered by Pygame."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from math import ceil, cos, sin
from pathlib import Path

import pygame

from . import brand as brand_assets


_ASSET_DIRECTORY = Path(__file__).with_name("icon_assets")

# Keep the names already used by the interface, but resolve them to familiar,
# consistent icons from Lucide instead of drawing each symbol by hand.
_ICON_FILES = {
    "close": "x",
    "remove": "x",
    "plus": "plus",
    "minus": "minus",
    "chevron": "chevron-right",
    "collapse": "panel-left-close",
    "expand": "chevron-down",
    "sun": "sun",
    "theme": "sun",
    "moon": "moon",
    "cube": "box",
    "brand": "renderx-mark",
    "object": "box",
    "wireframe": "box",
    "axes": "axis-3d",
    "move": "move-3d",
    "rotate": "rotate-ccw",
    "refresh": "rotate-ccw",
    "home": "home",
    "scale": "maximize-2",
    "fit": "maximize-2",
    "eye": "eye",
    "view": "eye",
    "folder": "folder-open",
    "import": "folder-open",
    "camera": "camera",
    "screenshot": "camera",
    "help": "circle-question-mark",
    "shortcuts": "circle-question-mark",
    "play": "play",
    "music_on": "volume-2",
    "music_off": "volume-x",
    "volume": "volume-2",
    "muted": "volume-x",
}


@lru_cache(maxsize=256)
def _icon_surface(name: str, width: int, height: int,
                  color: tuple[int, int, int]) -> pygame.Surface:
    """Load at the SVG's native viewBox, then scale to the requested size."""
    icon_path = _ASSET_DIRECTORY / f"{name}.svg"
    source = icon_path.read_bytes()
    color_hex = "#{:02x}{:02x}{:02x}".format(*color).encode()
    source = source.replace(b"currentColor", color_hex)
    rendered = pygame.image.load(BytesIO(source), icon_path.name)
    if rendered.get_size() != (width, height):
        rendered = pygame.transform.smoothscale(rendered, (width, height))
    rgb = pygame.surfarray.pixels3d(rendered)
    rgb[:] = color
    del rgb
    # Smooth scaling thin 24 px strokes down can leave every pixel slightly
    # translucent. Normalize the raster's strongest stroke back to solid so
    # small controls stay crisp on the dark surface behind them.
    alpha = pygame.surfarray.pixels_alpha(rendered)
    maximum_alpha = int(alpha.max())
    if 0 < maximum_alpha < 255:
        alpha[:] = (alpha.astype("uint16") * 255 // maximum_alpha).clip(0, 255)
    del alpha
    return rendered


def draw_icon(surface: pygame.Surface, name: str, rect: pygame.Rect,
              color: tuple[int, int, int], *, stroke: int | None = None) -> None:
    """Draw a sharp SVG centered in the control without stretching its shape."""
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    icon_rect = rect.inflate(-2, -2) if min(rect.size) >= 3 else rect
    if name == "brand":
        mark = brand_assets.mark(min(icon_rect.size))
        surface.blit(mark, mark.get_rect(center=icon_rect.center))
        return
    if name.startswith("shape:"):
        _draw_shape_icon(surface, name[6:], icon_rect, color)
        return
    icon_name = _ICON_FILES.get(name, name)
    side = min(icon_rect.width, icon_rect.height)
    if side <= 0:
        return
    icon_surface = _icon_surface(icon_name, side, side,
                                 tuple(map(int, color)))
    visible = icon_surface.get_bounding_rect(min_alpha=1)
    if visible.width == 0 or visible.height == 0:
        return
    x = icon_rect.centerx - visible.centerx
    y = icon_rect.centery - visible.centery
    # Center the visible strokes, not just the SVG viewBox. A few Lucide paths
    # (notably axis-3d) leave uneven transparent space in their source canvas.
    min_x = rect.left + 1 - visible.left
    max_x = rect.right - 1 - visible.right
    min_y = rect.top + 1 - visible.top
    max_y = rect.bottom - 1 - visible.bottom
    x = max(min_x, min(max_x, x))
    y = max(min_y, min(max_y, y))
    surface.blit(icon_surface, (x, y))


@lru_cache(maxsize=1)
def _shape_meshes():
    """Share the application's actual meshes with the scene-list previews."""
    from renderx.core.models import make_library

    return make_library()


@lru_cache(maxsize=128)
def _shape_icon_surface(name: str, side: int,
                        color: tuple[int, int, int]) -> pygame.Surface:
    mesh = _shape_meshes().get(name)
    if mesh is None:
        return _icon_surface("box", side, side, color)

    # Render larger, then reduce once for smooth, consistent 16 px linework.
    scale = 4
    canvas = pygame.Surface((side * scale, side * scale), pygame.SRCALPHA)
    vertices = mesh.vertices
    yaw, pitch = 0.72, 0.48
    cy, sy = cos(yaw), sin(yaw)
    cp, sp = cos(pitch), sin(pitch)
    projected = []
    for x, y, z in vertices:
        rotated_x = x * cy - z * sy
        rotated_z = x * sy + z * cy
        screen_y = -(y * cp - rotated_z * sp)
        projected.append((rotated_x, screen_y))

    min_x = min(point[0] for point in projected)
    max_x = max(point[0] for point in projected)
    min_y = min(point[1] for point in projected)
    max_y = max(point[1] for point in projected)
    span = max(max_x - min_x, max_y - min_y, 1e-6)
    margin = side * scale * 0.18
    fit = max(1.0, (side * scale - margin * 2) / span)
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    points = [
        (round(side * scale * 0.5 + (x - center_x) * fit),
         round(side * scale * 0.5 + (y - center_y) * fit))
        for x, y in projected
    ]

    # Highly tessellated meshes become mud at icon size. Evenly sample their
    # topology so each preview keeps its silhouette and remains legible.
    edge_step = max(1, ceil(len(mesh.edges) / 34))
    sampled_edges = mesh.edges[::edge_step]
    line_color = (*color, 255)
    for first, second in sampled_edges:
        pygame.draw.line(canvas, line_color, points[first], points[second],
                         max(2, scale))
    icon = pygame.transform.smoothscale(canvas, (side, side))
    icon.set_alpha(255)
    return icon


def _draw_shape_icon(surface: pygame.Surface, name: str, rect: pygame.Rect,
                     color: tuple[int, int, int]) -> None:
    side = min(rect.width, rect.height)
    icon_surface = _shape_icon_surface(name, side, tuple(map(int, color)))
    surface.blit(icon_surface, icon_surface.get_rect(center=rect.center))
