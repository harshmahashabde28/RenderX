"""Two projections of the same scene, using the existing camera and renderer."""
import pygame
from renderx import config
from renderx.axes import draw_axes
from renderx.renderer import VIEWPORT, draw_wireframe, draw_selected_vertex
from renderx.transform import transform_vertex

# Both views use the same zoom. k = f / default depth makes their sizes agree
# for a plane at depth 5. A smaller f fits both models in the narrower panes.
COMPARE_FOCAL_LENGTH = 300
GUIDE_COLOR = (171, 145, 227)
VIEWS = (
    ("Perspective", pygame.Rect(16, 200, 386, 420)),
    ("Orthographic", pygame.Rect(418, 200, 386, 420)),
)


def projected_bounds(world_points, edges, camera, mode, centre,
                     focal_length=COMPARE_FOCAL_LENGTH):
    """Bounds of projected near-clipped edges, before 2D viewport clipping."""
    points = []
    for start, end in edges:
        segment = camera.project_edge(world_points[start], world_points[end], mode,
                                      centre=centre, focal_length=focal_length)
        if segment is not None:
            points.extend(segment)
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def draw_guides(surface, viewport, bounds):
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(viewport))
    x, y = viewport.center
    pygame.draw.line(surface, config.MUTED, (x - 6, y), (x + 6, y))
    pygame.draw.line(surface, config.MUTED, (x, y - 6), (x, y + 6))
    if bounds is not None:
        left, top, right, bottom = bounds
        corners = [(left, top), (right, top), (right, bottom), (left, bottom)]
        pygame.draw.lines(surface, GUIDE_COLOR, True, corners, 1)
    surface.set_clip(previous_clip)


def draw_comparison(surface, mesh, scene, camera, learning, font):
    """Draw both panes without changing Scene, Camera, Mesh or LearningState."""
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(VIEWPORT))
    surface.fill(config.BACKGROUND, VIEWPORT)
    world_points = [transform_vertex(point, scene) for point in mesh.vertices]
    selected = world_points[learning.selected_vertex]
    for mode, viewport in VIEWS:
        draw_wireframe(surface, mesh, scene, camera, viewport=viewport,
                       projection=mode, focal_length=COMPARE_FOCAL_LENGTH)
        if scene.axes_visible:
            draw_axes(surface, camera, mode, font, viewport=viewport,
                      focal_length=COMPARE_FOCAL_LENGTH)
        bounds = projected_bounds(world_points, mesh.edges, camera, mode, viewport.center)
        if learning.guides_visible:
            draw_guides(surface, viewport, bounds)
        point = camera.project(selected, mode, centre=viewport.center,
                               focal_length=COMPARE_FOCAL_LENGTH)
        draw_selected_vertex(surface, point, learning.selected_vertex, font,
                             viewport=viewport)
        active = mode == scene.projection
        color = config.ACCENT if active else config.MUTED
        pygame.draw.rect(surface, color, viewport, 2 if active else 1)
        title = mode.upper() + ("  /  P SELECTED" if active else "")
        surface.blit(font.render(title, True, color), (viewport.left + 8, 177))
        f = COMPARE_FOCAL_LENGTH
        k = f / config.DEFAULT_DEPTH
        formula = (f"sx = cx + {f:g}*x/z; sy = cy - {f:g}*y/z" if mode == "Perspective"
                   else f"sx = cx + {k:g}*x; sy = cy - {k:g}*y")
        pygame.draw.rect(surface, config.PANEL,
                         (viewport.left + 6, viewport.top + 6, viewport.width - 12, 25))
        surface.blit(font.render(formula, True, config.TEXT),
                     (viewport.left + 12, viewport.top + 10))
        if point is None:
            coordinates = "not projected (hidden/invalid)"
        else:
            coordinates = f"({point[0]:.1f}, {point[1]:.1f}) px"
        surface.blit(font.render(f"v{learning.selected_vertex}: {coordinates}",
                                 True, config.SELECTED), (viewport.left + 8, 632))
        if bounds is None:
            size = "No visible edges"
        else:
            width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
            size = f"Projected bounds: {width:.1f} x {height:.1f} px"
        surface.blit(font.render(size, True, GUIDE_COLOR), (viewport.left + 8, 654))
    camera_text = ", ".join(f"{value:g}" for value in camera.position)
    surface.blit(font.render(f"Shared camera: ({camera_text})  |  Near plane: z = {config.NEAR_DEPTH:g}",
                             True, config.MUTED), (24, 105))
    surface.blit(font.render("PgUp / PgDn: change depth in BOTH views. Watch their sizes.",
                             True, config.TEXT), (24, 128))
    guides = "on" if learning.guides_visible else "off"
    surface.blit(font.render(f"V: guides {guides} (center + bounds)  |  , / .: select vertex  |  P: select projection",
                             True, config.MUTED), (24, 151))
    surface.set_clip(previous_clip)
