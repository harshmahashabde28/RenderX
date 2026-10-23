"""Projection comparison math used by the active challenge view."""

COMPARE_FOCAL_LENGTH = 300


def projected_bounds(world_points, edges, camera, mode, centre,
                     focal_length=COMPARE_FOCAL_LENGTH):
    """Bounds of near-clipped projected edges, before viewport clipping."""
    points = []
    for start, end in edges:
        segment = camera.project_edge(world_points[start], world_points[end], mode,
                                      centre=centre, focal_length=focal_length)
        if segment is not None:
            points.extend(segment)
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)
