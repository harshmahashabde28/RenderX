"""Vectorized NumPy acceleration for batch vertex transformations with pure-Python reference."""
from math import cos, sin
from typing import Sequence, Tuple, List, Optional
from renderx.core.transform import transform_vertex

Point3D = Tuple[float, float, float]
Point2D = Tuple[float, float]

_NUMPY_AVAILABLE = False
try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore


def has_numpy() -> bool:
    """Return True if NumPy is available in the runtime environment."""
    return _NUMPY_AVAILABLE


def batch_transform_pure(
    vertices: Sequence[Point3D],
    scale: float,
    angles: Point3D,
    position: Point3D,
) -> List[Point3D]:
    """Pure-Python reference implementation for batch vertex transformation."""
    ax, ay, az = angles
    px, py, pz = position
    cx, sx = cos(ax), sin(ax)
    cy, sy = cos(ay), sin(ay)
    cz, sz = cos(az), sin(az)

    transformed: list[Point3D] = []
    for x, y, z in vertices:
        # Scale
        x *= scale
        y *= scale
        z *= scale

        # Rx
        y_rx = y * cx - z * sx
        z_rx = y * sx + z * cx
        x_rx = x

        # Ry
        x_ry = x_rx * cy + z_rx * sy
        y_ry = y_rx
        z_ry = -x_rx * sy + z_rx * cy

        # Rz
        x_rz = x_ry * cz - y_ry * sz
        y_rz = x_ry * sz + y_ry * cz
        z_rz = z_ry

        # Translate
        transformed.append((x_rz + px, y_rz + py, z_rz + pz))
    return transformed


def batch_transform_numpy(
    vertices: Sequence[Point3D],
    scale: float,
    angles: Point3D,
    position: Point3D,
) -> List[Point3D]:
    """Vectorized NumPy implementation for batch vertex transformation."""
    if not _NUMPY_AVAILABLE or not vertices:
        return batch_transform_pure(vertices, scale, angles, position)

    v = np.asarray(vertices, dtype=np.float64) * scale

    ax, ay, az = angles
    cx, sx = cos(ax), sin(ax)
    cy, sy = cos(ay), sin(ay)
    cz, sz = cos(az), sin(az)

    # 3x3 rotation matrices transposed for row-vector multiplication: v @ R^T
    # Rx
    rx_t = np.array([
        [1.0, 0.0, 0.0],
        [0.0, cx, sx],
        [0.0, -sx, cx],
    ], dtype=np.float64)

    # Ry
    ry_t = np.array([
        [cy, 0.0, -sy],
        [0.0, 1.0, 0.0],
        [sy, 0.0, cy],
    ], dtype=np.float64)

    # Rz
    rz_t = np.array([
        [cz, sz, 0.0],
        [-sz, cz, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float64)

    # Combined rotation: v @ rx_t @ ry_t @ rz_t
    rot = rx_t @ ry_t @ rz_t
    rotated = v @ rot

    # Translation
    pos = np.array(position, dtype=np.float64)
    result = rotated + pos

    return [tuple(row) for row in result]  # type: ignore


def batch_transform(
    vertices: Sequence[Point3D],
    scale: float,
    angles: Point3D,
    position: Point3D,
    prefer_numpy: bool = True,
) -> List[Point3D]:
    """Transform a batch of vertices using NumPy if available, or pure-Python reference."""
    if prefer_numpy and _NUMPY_AVAILABLE and len(vertices) >= 32:
        return batch_transform_numpy(vertices, scale, angles, position)
    return batch_transform_pure(vertices, scale, angles, position)
