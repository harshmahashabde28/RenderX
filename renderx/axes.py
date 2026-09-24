"""World-aligned reference triad, independent of the object's transformations."""
import pygame
from renderx import config
from renderx.renderer import VIEWPORT

# Place the shared reference origin beside the model, ahead of the fixed camera.
# These are world coordinates, not a screen-space icon or object-local axes.
ORIGIN = (-2.3, -1.7, 5.0)
LENGTH = 1.2
AXES = [
    ("X", (ORIGIN[0] + LENGTH, ORIGIN[1], ORIGIN[2]), (244, 105, 109)),
    ("Y", (ORIGIN[0], ORIGIN[1] + LENGTH, ORIGIN[2]), (101, 222, 139)),
    ("Z", (ORIGIN[0], ORIGIN[1], ORIGIN[2] + LENGTH), (108, 163, 255)),
]


def draw_axes(surface, camera, mode, font, *, viewport=None, centre=None,
              focal_length=config.FOCAL_LENGTH):
    viewport = VIEWPORT if viewport is None else pygame.Rect(viewport)
    centre = viewport.center if centre is None else centre
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(viewport))
    drawn = 0
    for name, endpoint, color in AXES:
        tip = camera.project(endpoint, mode, centre=centre, focal_length=focal_length)
        segment = camera.project_edge(ORIGIN, endpoint, mode, centre=centre,
                                      focal_length=focal_length)
        if segment is None:
            continue
        pygame.draw.line(surface, color, segment[0], segment[1], 2)
        drawn += 1
        if tip is None:
            continue
        # With a Z-facing orthographic camera, the Z axis collapses to a point.
        pygame.draw.circle(surface, color, (round(tip[0]), round(tip[1])), 3)
        if viewport.collidepoint(tip):
            surface.blit(font.render(name, True, color), (tip[0] + 7, tip[1] - 9))
    surface.set_clip(previous_clip)
    return drawn
