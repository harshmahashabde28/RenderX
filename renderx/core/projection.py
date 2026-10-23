"""Perspective and orthographic camera projection mathematics."""
from math import isfinite
from typing import Tuple, Optional
from renderx import config

Point3D = Tuple[float, float, float]
Point2D = Tuple[float, float]


def project_point(
    point: Point3D,
    centre: Point2D = config.CENTRE,
    focal_length: float = config.FOCAL_LENGTH,
    near_depth: float = config.NEAR_DEPTH,
) -> Optional[Point2D]:
    """Project a 3D camera-space point onto a 2D screen surface in perspective.

    Formula:
        screen_x = centre_x + focal_length * x / z
        screen_y = centre_y - focal_length * y / z  (Screen Y points downwards)

    Returns None for non-finite inputs, points behind the supplied near plane,
    or points at/behind the camera plane. A clipped edge may end exactly on a
    positive near plane, where projection remains finite and visible.
    """
    x, y, z = point
    if (not all(isfinite(val) for val in (*point, *centre, focal_length, near_depth)) or
            z <= 0.0 or z < near_depth):
        return None  # Do not divide by zero or project behind the camera near plane
    projected = (
        centre[0] + focal_length * x / z,
        centre[1] - focal_length * y / z,
    )
    return projected if all(isfinite(value) for value in projected) else None


def project_perspective(
    point: Point3D,
    centre: Point2D = config.CENTRE,
    focal_length: float = config.FOCAL_LENGTH,
    near_depth: float = config.NEAR_DEPTH,
) -> Optional[Point2D]:
    """Alias for project_point."""
    return project_point(point, centre, focal_length, near_depth)


def project_orthographic(
    point: Point3D,
    centre: Point2D = config.CENTRE,
    scale: float = config.FOCAL_LENGTH / config.DEFAULT_DEPTH,
    near_depth: float = config.NEAR_DEPTH,
) -> Optional[Point2D]:
    """Project a 3D camera-space point using orthographic parallel projection.

    Formula:
        screen_x = centre_x + scale * x
        screen_y = centre_y - scale * y

    Orthographic projection does not scale by depth (Z), maintaining true parallel measurements.
    """
    x, y, z = point
    if (not all(isfinite(val) for val in (*point, *centre, scale, near_depth)) or
            z <= 0.0 or z < near_depth):
        return None
    projected = (centre[0] + x * scale, centre[1] - y * scale)
    return projected if all(isfinite(value) for value in projected) else None
