"""Fixed camera facing positive Z; perspective is calculated by hand."""
from dataclasses import dataclass
from math import isfinite
from renderx import config
from renderx.clipping import clip_edge_near


def project_point(point, centre=config.CENTRE,
                  focal_length=config.FOCAL_LENGTH,
                  near_depth=config.NEAR_DEPTH):
    x, y, z = point
    if not all(isfinite(value) for value in point) or z < near_depth:
        return None  # Do not divide by zero or project behind the camera.
    # Divide by depth: distant points have smaller offsets from the centre.
    return (centre[0] + focal_length * x / z,
            centre[1] - focal_length * y / z)  # Screen Y points down.


@dataclass
class Camera:
    position: tuple = (0.0, 0.0, 0.0)

    def relative_point(self, world_point):
        return tuple(value - camera_value for value, camera_value
                     in zip(world_point, self.position))

    def project(self, world_point, mode="Perspective"):
        return self.project_relative(self.relative_point(world_point), mode)

    def project_relative(self, point, mode="Perspective"):
        if mode == "Orthographic":
            return project_orthographic(point)
        return project_point(point)

    def project_edge(self, world_a, world_b, mode="Perspective"):
        clipped = clip_edge_near(self.relative_point(world_a),
                                 self.relative_point(world_b))
        if clipped is None:
            return None
        return tuple(self.project_relative(point, mode) for point in clipped)


def project_orthographic(point, centre=config.CENTRE,
                         scale=config.FOCAL_LENGTH / config.DEFAULT_DEPTH,
                         near_depth=config.NEAR_DEPTH):
    """Fixed pixels per world unit: depth does not change apparent size."""
    x, y, z = point
    if not all(isfinite(value) for value in point) or z < near_depth:
        return None
    return centre[0] + x * scale, centre[1] - y * scale
