"""Pure 3D transformation mathematics.

Coordinate convention:
- X points right.
- Y points up.
- Positive Z points away from the viewer (forward into the screen).

The transformation pipeline evaluates non-destructively in standard order:
    Scale -> Rotation X -> Rotation Y -> Rotation Z -> Translation
"""
from math import cos, sin
from typing import Any, Tuple

Point3D = Tuple[float, float, float]


def rotate_x(point: Point3D | tuple[float, float, float], angle: float) -> Point3D:
    """Rotate a point around the X axis by `angle` radians."""
    x, y, z = point
    c, s = cos(angle), sin(angle)
    return x, y * c - z * s, y * s + z * c


def rotate_y(point: Point3D | tuple[float, float, float], angle: float) -> Point3D:
    """Rotate a point around the Y axis by `angle` radians."""
    x, y, z = point
    c, s = cos(angle), sin(angle)
    return x * c + z * s, y, -x * s + z * c


def rotate_z(point: Point3D | tuple[float, float, float], angle: float) -> Point3D:
    """Rotate a point around the Z axis by `angle` radians."""
    x, y, z = point
    c, s = cos(angle), sin(angle)
    return x * c - y * s, x * s + y * c, z


def transform_stages(point: Point3D | tuple[float, float, float], scene: Any) -> Tuple[Point3D, ...]:
    """Return each intermediate coordinate tuple across the 5-stage transformation pipeline.

    Stages:
    0: Original model point
    1: Uniformly scaled
    2: Rotated around X
    3: Rotated around Y
    4: Rotated around Z
    5: Translated into world space
    """
    original = tuple(point)  # type: ignore
    scaled = tuple(value * scene.scale for value in original)
    x_rotated = rotate_x(scaled, scene.angles[0])
    y_rotated = rotate_y(x_rotated, scene.angles[1])
    z_rotated = rotate_z(y_rotated, scene.angles[2])
    translated = tuple(value + offset for value, offset in zip(z_rotated, scene.position))
    return original, scaled, x_rotated, y_rotated, z_rotated, translated  # type: ignore


def transform_vertex(point: Point3D | tuple[float, float, float], scene: Any) -> Point3D:
    """Transform a single model vertex into world space via Scale -> Rx -> Ry -> Rz -> Translate."""
    return transform_stages(point, scene)[-1]
