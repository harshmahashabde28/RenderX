"""Clip a camera-space line segment before dividing by depth."""
from math import isfinite
from renderx import config


def clip_edge_near(a, b, near_z=config.NEAR_DEPTH):
    """Return the visible endpoints, or None; points on the plane are visible."""
    if not all(isfinite(value) for point in (a, b) for value in point):
        return None
    if not isfinite(near_z) or near_z <= 0:
        raise ValueError("Near depth must be finite and positive.")
    a_inside, b_inside = a[2] >= near_z, b[2] >= near_z
    if a_inside and b_inside:
        return a, b
    if not a_inside and not b_inside:
        return None

    dz = b[2] - a[2]
    if abs(dz) < 1e-12:
        # A very shallow crossing: rescale distances before division.
        # This is the same t, without dividing by a tiny depth difference.
        da, db = abs(near_z - a[2]), abs(b[2] - near_z)
        largest = max(da, db)
        if largest == 0:
            return a, b
        da, db = da / largest, db / largest
        t = da / (da + db)
    else:
        t = (near_z - a[2]) / dz
    # A + t(B-A) finds where the edge intersects z = near_z.
    intersection = (a[0] + t * (b[0] - a[0]),
                    a[1] + t * (b[1] - a[1]), near_z)
    return (a, intersection) if a_inside else (intersection, b)
