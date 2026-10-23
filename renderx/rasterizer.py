"""Small software triangle rasterizer used by Explore's render modes.

The triangle coverage, perspective-correct depth interpolation, and depth test
are implemented here rather than delegated to a 3D engine. NumPy only provides
fast rectangular pixel operations; transforms, clipping, projection, and the
visibility decisions remain readable Python code.
"""
from math import floor, isfinite

import numpy as np
import pygame

from renderx import config
from renderx.renderer import draw_wireframe
from renderx.transform import transform_vertex

RENDER_MODES = ("Wireframe", "Hidden line", "Solid", "Depth")
_LIGHT = np.asarray((-0.42, 0.72, -0.55), dtype=np.float64)
_LIGHT /= np.linalg.norm(_LIGHT)


def draw_render_mode(surface, mesh, scene, camera, *, mode="Wireframe",
                     viewport=None, centre=None, focal_length=520):
    """Draw one model in wireframe, hidden-line, shaded, or depth mode."""
    viewport = pygame.Rect(surface.get_rect() if viewport is None else viewport)
    centre = viewport.center if centre is None else centre
    if mode not in RENDER_MODES:
        raise ValueError(f"Unknown render mode: {mode}")
    if mode == "Wireframe" or not mesh.faces:
        draw_wireframe(surface, mesh, scene, camera, viewport=viewport,
                       centre=centre, focal_length=focal_length)
        return {"mode": mode, "faces": len(mesh.faces or []),
                "triangles": 0, "pixels": 0,
                "wire_only": mode != "Wireframe"}

    width, height = viewport.size
    depth = np.full((height, width), np.inf, dtype=np.float32)
    colors = np.zeros((height, width, 3), dtype=np.uint8)
    old_clip = surface.get_clip()
    surface.set_clip(old_clip.clip(viewport))
    _draw_background(surface, viewport)

    world_points = [transform_vertex(point, scene) for point in mesh.vertices]
    camera_points = [camera.relative_point(point) for point in world_points]
    triangles_drawn = 0
    for face in mesh.faces:
        for indices in _triangulate_face(face, camera_points):
            triangle = [camera_points[index] for index in indices]
            clipped = _clip_near(triangle)
            if len(clipped) < 3:
                continue
            for index in range(1, len(clipped) - 1):
                clipped_triangle = (clipped[0], clipped[index], clipped[index + 1])
                projected = tuple(_project(point, scene.projection, centre,
                                           focal_length)
                                  for point in clipped_triangle)
                color = _face_color(triangle, mode) if mode == "Solid" else None
                if _raster_triangle(surface, projected, clipped_triangle,
                                    viewport, depth, colors, color,
                                    scene.projection):
                    triangles_drawn += 1

    if mode == "Depth":
        _colorize_depth(depth, colors)
    # Pygame's surfarray exposes pixels as [x, y, channel]; release the view
    # before drawing the edge pass, which needs to lock the same surface.
    pixel_view = pygame.surfarray.pixels3d(surface)
    pixel_view[viewport.left:viewport.right,
               viewport.top:viewport.bottom] = colors.transpose(1, 0, 2)
    del pixel_view

    def depth_visible(point):
        screen = _project(point, scene.projection, centre, focal_length)
        local_x = round(screen[0] - viewport.left)
        local_y = round(screen[1] - viewport.top)
        if not (0 <= local_x < width and 0 <= local_y < height):
            return False
        nearest = float(depth[local_y, local_x])
        tolerance = max(0.025, point[2] * 0.002)
        return not isfinite(nearest) or point[2] <= nearest + tolerance

    if mode == "Hidden line":
        line_color, line_width = config.ACCENT, 2
        vertex_color, vertex_radius = config.TEXT, 2
    elif mode == "Solid":
        line_color, line_width = (37, 83, 77), 1
        vertex_color, vertex_radius = (239, 249, 246), 2
    else:
        line_color, line_width = (24, 38, 53), 1
        vertex_color, vertex_radius = (32, 48, 65), 1
    draw_wireframe(surface, mesh, scene, camera, viewport=viewport,
                   centre=centre, focal_length=focal_length,
                   line_color=line_color, vertex_color=vertex_color,
                   clear=False, show_vertices=mode != "Depth",
                   edge_visibility=depth_visible, visibility_step=2,
                   line_width=line_width, vertex_radius=vertex_radius)
    surface.set_clip(old_clip)
    return {"mode": mode, "faces": len(mesh.faces),
            "triangles": triangles_drawn,
            "pixels": int(np.isfinite(depth).sum()), "wire_only": False}


def _draw_background(surface, viewport):
    surface.fill(config.BACKGROUND, viewport)
    for x in range(viewport.left + 10, viewport.right, 40):
        pygame.draw.line(surface, config.GRID, (x, viewport.top),
                         (x, viewport.bottom))
    for y in range(viewport.top + 10, viewport.bottom, 40):
        pygame.draw.line(surface, config.GRID, (viewport.left, y),
                         (viewport.right, y))


def _triangulate_face(face, points):
    """Ear-clip a planar polygon after projecting it onto its dominant plane."""
    if len(face) == 3:
        return [(face[0], face[1], face[2])]
    normal = np.zeros(3, dtype=np.float64)
    for start, end in zip(face, face[1:] + face[:1]):
        a, b = points[start], points[end]
        normal[0] += (a[1] - b[1]) * (a[2] + b[2])
        normal[1] += (a[2] - b[2]) * (a[0] + b[0])
        normal[2] += (a[0] - b[0]) * (a[1] + b[1])
    axis = int(np.argmax(np.abs(normal)))
    if axis == 0:
        projected = [(points[index][1], points[index][2]) for index in face]
    elif axis == 1:
        projected = [(points[index][0], points[index][2]) for index in face]
    else:
        projected = [(points[index][0], points[index][1]) for index in face]
    area = sum(projected[i][0] * projected[(i + 1) % len(face)][1] -
               projected[(i + 1) % len(face)][0] * projected[i][1]
               for i in range(len(face)))
    if abs(area) < 1e-10:
        return [(face[0], face[i], face[i + 1])
                for i in range(1, len(face) - 1)]
    orientation = 1 if area > 0 else -1
    remaining = list(range(len(face)))
    result = []

    def cross(a, b, c):
        return ((b[0] - a[0]) * (c[1] - a[1]) -
                (b[1] - a[1]) * (c[0] - a[0]))

    def inside(point, a, b, c):
        values = (cross(a, b, point), cross(b, c, point),
                  cross(c, a, point))
        return all(value >= -1e-9 for value in values) or all(
            value <= 1e-9 for value in values)

    while len(remaining) > 3:
        ear = None
        for position, current in enumerate(remaining):
            previous = remaining[position - 1]
            following = remaining[(position + 1) % len(remaining)]
            a, b, c = (projected[previous], projected[current],
                       projected[following])
            if cross(a, b, c) * orientation <= 1e-10:
                continue
            if any(inside(projected[other], a, b, c)
                   for other in remaining
                   if other not in (previous, current, following)):
                continue
            ear = (previous, current, following)
            result.append(tuple(face[index] for index in ear))
            remaining.remove(current)
            break
        if ear is None:
            return [(face[0], face[i], face[i + 1])
                    for i in range(1, len(face) - 1)]
    result.append(tuple(face[index] for index in remaining))
    return result


def _clip_near(points):
    """Clip a camera-space polygon before perspective division."""
    output = []
    previous = points[-1]
    previous_inside = previous[2] >= config.NEAR_DEPTH
    for current in points:
        current_inside = current[2] >= config.NEAR_DEPTH
        if current_inside != previous_inside:
            amount = ((config.NEAR_DEPTH - previous[2]) /
                      (current[2] - previous[2]))
            output.append(tuple(previous[axis] +
                                (current[axis] - previous[axis]) * amount
                                for axis in range(3)))
        if current_inside:
            output.append(current)
        previous, previous_inside = current, current_inside
    return output


def _project(point, projection, centre, focal_length):
    x, y, z = point
    if projection == "Orthographic":
        scale = focal_length / config.DEFAULT_DEPTH
        return centre[0] + x * scale, centre[1] - y * scale
    return centre[0] + focal_length * x / z, centre[1] - focal_length * y / z


def _face_color(points, mode):
    if mode == "Hidden line":
        return (43, 59, 72)
    a, b, c = (np.asarray(point, dtype=np.float64) for point in points)
    normal = np.cross(b - a, c - a)
    length = float(np.linalg.norm(normal))
    lighting = 0.0 if length < 1e-12 else abs(float(np.dot(normal, _LIGHT))) / length
    brightness = 0.48 + 0.45 * lighting
    material = np.asarray((127, 185, 176), dtype=np.float64)
    return tuple(np.clip(material * brightness, 0, 255).astype(np.uint8))


def _raster_triangle(surface, projected, camera_points, viewport, depth_buffer,
                    color_buffer, color, projection):
    if any(not all(isfinite(value) for value in point) for point in projected):
        return False
    global_x = [point[0] for point in projected]
    global_y = [point[1] for point in projected]
    left = max(0, floor(min(global_x) - viewport.left))
    right = min(viewport.width - 1, floor(max(global_x) - viewport.left))
    top = max(0, floor(min(global_y) - viewport.top))
    bottom = min(viewport.height - 1, floor(max(global_y) - viewport.top))
    if left > right or top > bottom:
        return False

    x0, y0 = projected[0]
    x1, y1 = projected[1]
    x2, y2 = projected[2]
    denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denominator) < 1e-10:
        return False
    xs, ys = np.meshgrid(np.arange(left, right + 1, dtype=np.float64) + viewport.left,
                         np.arange(top, bottom + 1, dtype=np.float64) + viewport.top)
    weight0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / denominator
    weight1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / denominator
    weight2 = 1.0 - weight0 - weight1
    covered = ((weight0 >= -1e-8) & (weight1 >= -1e-8) &
               (weight2 >= -1e-8))
    z0, z1, z2 = (point[2] for point in camera_points)
    if projection == "Orthographic":
        pixel_depth = weight0 * z0 + weight1 * z1 + weight2 * z2
    else:
        inverse_z = weight0 / z0 + weight1 / z1 + weight2 / z2
        pixel_depth = 1.0 / np.maximum(inverse_z, 1e-12)
    depth_slice = depth_buffer[top:bottom + 1, left:right + 1]
    closer = covered & (pixel_depth < depth_slice)
    if not np.any(closer):
        return False
    depth_slice[closer] = pixel_depth[closer]
    if color is not None:
        color_buffer[top:bottom + 1, left:right + 1][closer] = color
    return True


def _colorize_depth(depth, colors):
    visible = np.isfinite(depth)
    if not np.any(visible):
        return
    values = depth[visible]
    low, high = float(values.min()), float(values.max())
    amount = np.full(values.shape, 0.5, dtype=np.float64) if high - low < 1e-8 else (
        (values - low) / (high - low))
    stops = (0.0, 0.52, 1.0)
    palette = ((245, 169, 139), (177, 169, 225), (139, 211, 198))
    for channel in range(3):
        colors[..., channel][visible] = np.interp(
            amount, stops, [shade[channel] for shade in palette]).astype(np.uint8)
