"""3D near-plane clipping and 2D viewport line clipping algorithms."""
from math import isfinite
from typing import Tuple, Optional
from renderx import config

Point3D = Tuple[float, float, float]
Point2D = Tuple[float, float]


def clip_edge_near(
    a: Point3D, b: Point3D, near_z: float = config.NEAR_DEPTH
) -> Optional[Tuple[Point3D, Point3D]]:
    """Clip a 3D line segment against the camera near plane z = near_z.

    Returns the clipped segment endpoints (A', B'), or None if completely behind the plane.
    Points exactly on the near plane are considered visible.
    """
    if not all(isfinite(val) for pt in (a, b) for val in pt):
        return None
    if not isfinite(near_z) or near_z <= 0:
        raise ValueError("Near depth must be finite and positive.")

    a_inside = a[2] >= near_z
    b_inside = b[2] >= near_z

    if a_inside and b_inside:
        return a, b
    if not a_inside and not b_inside:
        return None

    dz = b[2] - a[2]
    if abs(dz) < 1e-12:
        # A very shallow crossing: rescale distances before division.
        da, db = abs(near_z - a[2]), abs(b[2] - near_z)
        largest = max(da, db)
        if largest == 0:
            return a, b
        da, db = da / largest, db / largest
        t = da / (da + db)
    else:
        t = (near_z - a[2]) / dz

    # A + t(B - A) finds where the edge intersects z = near_z.
    intersection = (
        a[0] + t * (b[0] - a[0]),
        a[1] + t * (b[1] - a[1]),
        near_z,
    )
    return (a, intersection) if a_inside else (intersection, b)


def clip_line_2d_liang_barsky(
    p1: Point2D,
    p2: Point2D,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
) -> Optional[Tuple[Point2D, Point2D]]:
    """Clip a 2D line segment against an axis-aligned viewport rectangle via Liang-Barsky.

    Guarantees no out-of-bounds coordinates reach 2D drawing routines.
    Returns (p1_clipped, p2_clipped) or None if entirely outside.
    """
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1

    p = (-dx, dx, -dy, dy)
    q = (x1 - xmin, xmax - x1, y1 - ymin, ymax - y1)

    t0, t1 = 0.0, 1.0

    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return None  # Parallel and entirely outside
        else:
            t = qi / pi
            if pi < 0:
                if t > t0:
                    t0 = t
            else:
                if t < t1:
                    t1 = t
            if t0 > t1:
                return None  # Segment outside

    clipped_p1 = (x1 + t0 * dx, y1 + t0 * dy)
    clipped_p2 = (x1 + t1 * dx, y1 + t1 * dy)
    return clipped_p1, clipped_p2


# Outcodes for Cohen-Sutherland
INSIDE = 0  # 0000
LEFT = 1    # 0001
RIGHT = 2   # 0010
BOTTOM = 4  # 0100
TOP = 8     # 1000


def _compute_outcode(x: float, y: float, xmin: float, ymin: float, xmax: float, ymax: float) -> int:
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP
    return code


def clip_line_2d_cohen_sutherland(
    p1: Point2D,
    p2: Point2D,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
) -> Optional[Tuple[Point2D, Point2D]]:
    """Alternative 2D line clipping via Cohen-Sutherland outcodes."""
    x0, y0 = p1
    x1, y1 = p2

    outcode0 = _compute_outcode(x0, y0, xmin, ymin, xmax, ymax)
    outcode1 = _compute_outcode(x1, y1, xmin, ymin, xmax, ymax)

    while True:
        if not (outcode0 | outcode1):
            # Both inside
            return (x0, y0), (x1, y1)
        if outcode0 & outcode1:
            # Both outside same region
            return None

        # Pick endpoint outside
        outcode_out = outcode0 if outcode0 else outcode1

        if outcode_out & TOP:
            x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
            y = ymax
        elif outcode_out & BOTTOM:
            x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
            y = ymin
        elif outcode_out & RIGHT:
            y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
            x = xmax
        elif outcode_out & LEFT:
            y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
            x = xmin
        else:
            x, y = x0, y0

        if outcode_out == outcode0:
            x0, y0 = x, y
            outcode0 = _compute_outcode(x0, y0, xmin, ymin, xmax, ymax)
        else:
            x1, y1 = x, y
            outcode1 = _compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
