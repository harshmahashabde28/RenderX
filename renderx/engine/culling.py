"""Geometric culling utilities: distance culling, back-face culling, and frustum culling."""
from math import sqrt
from typing import Tuple

Point3D = Tuple[float, float, float]


def distance_squared(p1: Point3D, p2: Point3D) -> float:
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    dz = p1[2] - p2[2]
    return dx * dx + dy * dy + dz * dz


def is_within_distance(point: Point3D, camera_pos: Point3D, max_dist: float) -> bool:
    """Return True if point is within max_dist of camera_pos."""
    return distance_squared(point, camera_pos) <= max_dist * max_dist


def calculate_face_normal(v0: Point3D, v1: Point3D, v2: Point3D) -> Point3D:
    """Compute normalized surface normal for a triangle using right-hand rule (counter-clockwise)."""
    # Edge vectors e1 = v1 - v0, e2 = v2 - v0
    e1x, e1y, e1z = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
    e2x, e2y, e2z = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]

    # Cross product e1 x e2
    nx = e1y * e2z - e1z * e2y
    ny = e1z * e2x - e1x * e2z
    nz = e1x * e2y - e1y * e2x

    length = sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0:
        return (0.0, 0.0, 1.0)
    return (nx / length, ny / length, nz / length)


def is_backface(v0: Point3D, v1: Point3D, v2: Point3D, camera_pos: Point3D) -> bool:
    """Check if a face in world space is facing away from the camera.

    Dot product between face normal and view vector (v0 - camera_pos) > 0 means pointing away.
    """
    normal = calculate_face_normal(v0, v1, v2)
    view_x = v0[0] - camera_pos[0]
    view_y = v0[1] - camera_pos[1]
    view_z = v0[2] - camera_pos[2]
    dot = normal[0] * view_x + normal[1] * view_y + normal[2] * view_z
    return dot > 0.0
