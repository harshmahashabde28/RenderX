"""Turn transformed 3D vertices into Pygame's 2D lines."""
import pygame
from renderx import config
from renderx.transform import transform_vertex

VIEWPORT = pygame.Rect(0, 0, config.VIEW_WIDTH, config.HEIGHT)


def draw_wireframe(surface, mesh, scene, camera):
    previous_clip = surface.get_clip()
    surface.set_clip(VIEWPORT)
    surface.fill(config.BACKGROUND, VIEWPORT)
    # This is a screen-space reference grid, not a 3D ground plane.
    for x in range(10, config.VIEW_WIDTH, 40):
        pygame.draw.line(surface, config.GRID, (x, 0), (x, config.HEIGHT))
    for y in range(10, config.HEIGHT, 40):
        pygame.draw.line(surface, config.GRID, (0, y), (config.VIEW_WIDTH, y))
    projected = [camera.project(transform_vertex(point, scene))
                 for point in mesh.vertices]
    drawn = 0
    for start, end in mesh.edges:
        if projected[start] is not None and projected[end] is not None:
            pygame.draw.line(surface, config.ACCENT,
                             projected[start], projected[end], 2)
            drawn += 1
    for point in projected:
        if point is not None:
            pygame.draw.circle(surface, config.TEXT,
                               (round(point[0]), round(point[1])), 3)
    surface.set_clip(previous_clip)
    return drawn
