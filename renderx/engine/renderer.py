"""Software wireframe and surface rasterizer with 2D viewport clipping and render styles."""
from math import ceil
from typing import Callable, Optional, Sequence, Tuple
import pygame

from renderx import config
from renderx.core.clipping import clip_edge_near, clip_line_2d_liang_barsky
from renderx.core.transform import transform_vertex
from renderx.engine.culling import is_backface, calculate_face_normal
from renderx.engine.styles import RenderStyle

VIEWPORT = pygame.Rect(0, 0, config.VIEW_WIDTH, config.HEIGHT)
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]
Color = Tuple[int, int, int]


def _interpolate_color(c1: Color, c2: Color, factor: float) -> Color:
    """Linearly interpolate between two RGB colors (factor 0.0 -> c1, factor 1.0 -> c2)."""
    f = max(0.0, min(1.0, factor))
    return (
        int(c1[0] + (c2[0] - c1[0]) * f),
        int(c1[1] + (c2[1] - c1[1]) * f),
        int(c1[2] + (c2[2] - c1[2]) * f),
    )


def draw_wireframe(
    surface: pygame.Surface,
    mesh,
    scene,
    camera,
    *,
    viewport: Optional[pygame.Rect] = None,
    centre: Optional[Point2D] = None,
    projection: Optional[str] = None,
    focal_length: float = config.FOCAL_LENGTH,
    line_color: Color = config.ACCENT,
    vertex_color: Color = config.TEXT,
    clear: bool = True,
    show_vertices: bool = True,
    edge_visibility: Optional[Callable[[Point3D], bool]] = None,
    visibility_step: int = 96,
    line_width: int = 2,
    vertex_radius: int = 3,
    render_style: RenderStyle = RenderStyle.WIREFRAME,
    fade_start_depth: float = 3.0,
    fade_end_depth: float = 25.0,
) -> int:
    """Render a 3D mesh to a 2D surface with clipping, culling, and chosen style."""
    viewport = VIEWPORT if viewport is None else pygame.Rect(viewport)
    centre = viewport.center if centre is None else centre
    projection = scene.projection if projection is None else projection
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(viewport))

    if clear:
        surface.fill(config.BACKGROUND, viewport)
        # Background reference grid
        for x in range(viewport.left + 10, viewport.right, 40):
            pygame.draw.line(surface, config.GRID, (x, viewport.top), (x, viewport.bottom))
        for y in range(viewport.top + 10, viewport.bottom, 40):
            pygame.draw.line(surface, config.GRID, (viewport.left, y), (viewport.right, y))

    world_points = [transform_vertex(point, scene) for point in mesh.vertices]
    camera_points = [camera.to_camera_space(pt) for pt in world_points]

    # Optional Solid rendering mode
    if render_style == RenderStyle.SOLID and mesh.faces:
        _draw_solid_faces(
            surface,
            mesh,
            world_points,
            camera_points,
            camera,
            projection,
            centre,
            focal_length,
            viewport,
            base_color=line_color,
        )

    # Project vertices for vertex display if requested
    projected = None
    if show_vertices or render_style == RenderStyle.VERTICES:
        projected = [
            camera.project_relative(pt, projection, centre=centre, focal_length=focal_length)
            for pt in camera_points
        ]

    drawn = 0
    xmin, ymin, xmax, ymax = float(viewport.left), float(viewport.top), float(viewport.right), float(viewport.bottom)

    for start, end in mesh.edges:
        pt_a = camera_points[start]
        pt_b = camera_points[end]

        # 1. 3D Near-Plane Clipping
        clipped_3d = clip_edge_near(pt_a, pt_b)
        if clipped_3d is None:
            continue

        c_a, c_b = clipped_3d
        p2d_a = camera.project_relative(c_a, projection, centre=centre, focal_length=focal_length)
        p2d_b = camera.project_relative(c_b, projection, centre=centre, focal_length=focal_length)

        if p2d_a is None or p2d_b is None:
            continue

        # 2. 2D Viewport Line Clipping (Liang-Barsky)
        clipped_2d = clip_line_2d_liang_barsky(p2d_a, p2d_b, xmin, ymin, xmax, ymax)
        if clipped_2d is None:
            continue

        screen_a, screen_b = clipped_2d

        # Determine effective line color based on style
        draw_color = line_color
        if render_style == RenderStyle.DEPTH_FADE:
            mid_z = (c_a[2] + c_b[2]) * 0.5
            fade = (mid_z - fade_start_depth) / max(0.1, fade_end_depth - fade_start_depth)
            draw_color = _interpolate_color(line_color, config.BACKGROUND, fade)
        elif render_style == RenderStyle.XRAY:
            # Subtle dimming for background edges
            draw_color = line_color

        if edge_visibility is None:
            pygame.draw.line(surface, draw_color, screen_a, screen_b, line_width)
            drawn += 1
        else:
            if _draw_visible_edge(
                surface,
                (screen_a, screen_b),
                clipped_3d,
                centre,
                projection,
                focal_length,
                edge_visibility,
                draw_color,
                visibility_step=visibility_step,
                line_width=line_width,
            ):
                drawn += 1

    # Draw vertices if requested
    if (show_vertices or render_style == RenderStyle.VERTICES) and projected is not None:
        for point in projected:
            if point is not None and viewport.collidepoint(point):
                pygame.draw.circle(
                    surface,
                    vertex_color,
                    (round(point[0]), round(point[1])),
                    vertex_radius,
                )

    surface.set_clip(previous_clip)
    return drawn


def _draw_solid_faces(
    surface: pygame.Surface,
    mesh,
    world_points: list[Point3D],
    camera_points: list[Point3D],
    camera,
    projection: str,
    centre: Point2D,
    focal_length: float,
    viewport: pygame.Rect,
    base_color: Color,
) -> None:
    """Draw solid shaded faces using Painter's algorithm depth sorting."""
    faces_to_render = []
    light_dir = (0.577, 0.577, -0.577)

    for face in mesh.faces:
        if len(face) < 3:
            continue
        v0 = world_points[face[0]]
        v1 = world_points[face[1]]
        v2 = world_points[face[2]]

        # Backface culling
        if is_backface(v0, v1, v2, camera.position):
            continue

        # Average camera depth for sorting
        cam_pts = [camera_points[idx] for idx in face]
        if any(pt[2] <= config.NEAR_DEPTH for pt in cam_pts):
            continue  # Skip partially clipped faces in solid mode for stability

        avg_z = sum(pt[2] for pt in cam_pts) / len(cam_pts)
        norm = calculate_face_normal(v0, v1, v2)
        # Dot product for diffuse lighting
        dot = max(0.15, norm[0] * light_dir[0] + norm[1] * light_dir[1] + norm[2] * light_dir[2])
        shaded_color = (
            int(base_color[0] * dot * 0.7),
            int(base_color[1] * dot * 0.7),
            int(base_color[2] * dot * 0.7),
        )

        # 2D Screen points
        poly_2d = []
        all_valid = True
        for pt in cam_pts:
            p2d = camera.project_relative(pt, projection, centre=centre, focal_length=focal_length)
            if p2d is None:
                all_valid = False
                break
            poly_2d.append(p2d)

        if all_valid and len(poly_2d) >= 3:
            faces_to_render.append((avg_z, poly_2d, shaded_color))

    # Sort furthest to nearest (Painter's algorithm)
    faces_to_render.sort(key=lambda item: item[0], reverse=True)

    for _, poly, color in faces_to_render:
        pygame.draw.polygon(surface, color, poly)


def _draw_visible_edge(
    surface: pygame.Surface,
    segment: Tuple[Point2D, Point2D],
    camera_edge: Tuple[Point3D, Point3D],
    centre: Point2D,
    projection: str,
    focal_length: float,
    visibility: Callable[[Point3D], bool],
    color: Color,
    *,
    visibility_step: int = 96,
    line_width: int = 2,
) -> bool:
    """Draw visible portions of a projected edge using a camera-space test."""
    (x0, y0), (x1, y1) = segment
    screen_length = max(abs(x1 - x0), abs(y1 - y0))
    steps = max(1, ceil(screen_length / max(1, visibility_step)))
    start, end = camera_edge
    visible_any = False

    def is_visible(t: float) -> bool:
        screen_x = x0 + (x1 - x0) * t
        screen_y = y0 + (y1 - y0) * t
        if projection == "Orthographic":
            scale = focal_length / config.DEFAULT_DEPTH
            point = (
                (screen_x - centre[0]) / scale,
                -(screen_y - centre[1]) / scale,
                start[2] + (end[2] - start[2]) * t,
            )
        else:
            inverse_depth = (1.0 - t) / start[2] + t / end[2]
            depth = 1.0 / max(1e-6, inverse_depth)
            point = (
                (screen_x - centre[0]) * depth / focal_length,
                -(screen_y - centre[1]) * depth / focal_length,
                depth,
            )
        return visibility(point)

    def transition(left: float, right: float, left_visible: bool) -> float:
        for _ in range(8):
            middle = (left + right) * 0.5
            if is_visible(middle) == left_visible:
                left = middle
            else:
                right = middle
        return (left + right) * 0.5

    def draw_interval(first_t: float, last_t: float) -> None:
        nonlocal visible_any
        if last_t <= first_t:
            return
        first = (x0 + (x1 - x0) * first_t, y0 + (y1 - y0) * first_t)
        last = (x0 + (x1 - x0) * last_t, y0 + (y1 - y0) * last_t)
        pygame.draw.line(surface, color, first, last, line_width)
        visible_any = True

    previous_t = 0.0
    previous_visible = is_visible(previous_t)
    run_start = 0.0 if previous_visible else None
    for index in range(1, steps + 1):
        current_t = index / steps
        current_visible = is_visible(current_t)
        if current_visible != previous_visible:
            boundary = transition(previous_t, current_t, previous_visible)
            if previous_visible:
                if run_start is not None:
                    draw_interval(run_start, boundary)
                run_start = None
            else:
                run_start = boundary
        previous_t = current_t
        previous_visible = current_visible

    if previous_visible and run_start is not None:
        draw_interval(run_start, 1.0)
    return visible_any


def draw_selected_vertex(
    surface: pygame.Surface,
    screen_point: Optional[Point2D],
    vertex_index: int,
    font: pygame.font.Font,
    *,
    viewport: Optional[pygame.Rect] = None,
) -> bool:
    """Highlight the final projected position, regardless of inspected stage."""
    viewport = VIEWPORT if viewport is None else pygame.Rect(viewport)
    if screen_point is None or not viewport.collidepoint(screen_point):
        return False
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(viewport))
    centre = (round(screen_point[0]), round(screen_point[1]))
    pygame.draw.circle(surface, config.SELECTED, centre, 9, 2)
    pygame.draw.circle(surface, config.SELECTED, centre, 4)
    label = font.render(f"v{vertex_index}", True, config.SELECTED)
    x = max(viewport.left + 4, min(centre[0] + 12, viewport.right - label.get_width() - 4))
    y = max(viewport.top + 4, min(centre[1] - 20, viewport.bottom - label.get_height() - 4))
    surface.blit(label, (x, y))
    surface.set_clip(previous_clip)
    return True
