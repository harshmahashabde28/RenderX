"""Turn transformed 3D vertices into Pygame's 2D lines."""
import pygame
from renderx import config
from renderx.transform import transform_vertex

VIEWPORT = pygame.Rect(0, 0, config.VIEW_WIDTH, config.HEIGHT)


def draw_wireframe(surface, mesh, scene, camera, *, viewport=None, centre=None,
                   projection=None, focal_length=config.FOCAL_LENGTH):
    viewport = VIEWPORT if viewport is None else pygame.Rect(viewport)
    centre = viewport.center if centre is None else centre
    projection = scene.projection if projection is None else projection
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(viewport))
    surface.fill(config.BACKGROUND, viewport)
    # This is a screen-space reference grid, not a 3D ground plane.
    for x in range(viewport.left + 10, viewport.right, 40):
        pygame.draw.line(surface, config.GRID, (x, viewport.top), (x, viewport.bottom))
    for y in range(viewport.top + 10, viewport.bottom, 40):
        pygame.draw.line(surface, config.GRID, (viewport.left, y), (viewport.right, y))
    world_points = [transform_vertex(point, scene) for point in mesh.vertices]
    projected = [camera.project(point, projection, centre=centre,
                                focal_length=focal_length) for point in world_points]
    drawn = 0
    for start, end in mesh.edges:
        segment = camera.project_edge(world_points[start], world_points[end],
                                      projection, centre=centre,
                                      focal_length=focal_length)
        if segment is not None:
            pygame.draw.line(surface, config.ACCENT, segment[0], segment[1], 2)
            drawn += 1
    for point in projected:
        if point is not None:
            pygame.draw.circle(surface, config.TEXT,
                               (round(point[0]), round(point[1])), 3)
    surface.set_clip(previous_clip)
    return drawn


def draw_selected_vertex(surface, screen_point, vertex_index, font, *, viewport=None):
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
    # Keep the label inside the viewport even near its right/bottom edges.
    x = max(viewport.left + 4,
            min(centre[0] + 12, viewport.right - label.get_width() - 4))
    y = max(viewport.top + 4,
            min(centre[1] - 20, viewport.bottom - label.get_height() - 4))
    surface.blit(label, (x, y))
    surface.set_clip(previous_clip)
    return True
