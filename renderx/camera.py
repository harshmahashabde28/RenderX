"""Fixed camera facing positive Z; perspective is calculated by hand."""
from dataclasses import dataclass
from math import isfinite
from renderx import config


def project_point(point, centre=config.CENTRE,
                  focal_length=config.FOCAL_LENGTH,
                  near_depth=config.NEAR_DEPTH):
    x, y, z = point
    if not all(isfinite(value) for value in point) or z <= near_depth:
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

    def project(self, world_point):
        return project_point(self.relative_point(world_point))
