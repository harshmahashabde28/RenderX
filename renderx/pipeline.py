"""Read-only snapshots of the same calculations used by the renderer."""
from dataclasses import dataclass
from renderx import config
from renderx.transform import transform_stages


@dataclass(frozen=True)
class PipelineStage:
    name: str
    coordinates: tuple | None
    formula: tuple[str, ...]
    explanation: str


def snapshot_vertex(point, scene, camera):
    """Trace one original point. None means it cannot be projected safely.

    Clipping belongs to edges, not individual vertices. A hidden vertex has no
    screen point, although an edge connected to it may remain partly visible.
    """
    original, scaled, rx, ry, rz, world = transform_stages(point, scene)
    relative = camera.relative_point(world)
    screen = camera.project_relative(relative, scene.projection)
    stages = [
        PipelineStage("Original model coordinates", original,
                      ("p = (x, y, z)",),
                      "The stored model point. Transformations never change it."),
        PipelineStage("Scaled coordinates", scaled,
                      ("(x', y', z') = (s*x, s*y, s*z)",),
                      "Multiply every coordinate by the same scale s."),
        PipelineStage("X-rotated coordinates", rx,
                      ("x' = x", "y' = y*cos(a) - z*sin(a)",
                       "z' = y*sin(a) + z*cos(a)"),
                      "a is the X angle in radians. X stays fixed; Y and Z rotate."),
        PipelineStage("Y-rotated coordinates", ry,
                      ("x' = x*cos(a) + z*sin(a)", "y' = y",
                       "z' = -x*sin(a) + z*cos(a)"),
                      "a is the Y angle in radians. Y stays fixed; X and Z rotate."),
        PipelineStage("Z-rotated coordinates", rz,
                      ("x' = x*cos(a) - y*sin(a)",
                       "y' = x*sin(a) + y*cos(a)", "z' = z"),
                      "a is the Z angle in radians. Z stays fixed; X and Y rotate."),
        PipelineStage("Translated world coordinates", world,
                      ("(x', y', z') = (x+tx, y+ty, z+tz)",),
                      "Add the object position after scaling and rotating."),
        PipelineStage("Camera-relative coordinates", relative,
                      ("p_camera = p_world - camera_position",),
                      "Subtract the camera position. Positive Z points away."),
    ]
    if scene.projection == "Orthographic":
        formula = ("screen_x = cx + k*x", "screen_y = cy - k*y",
                   f"k = {config.FOCAL_LENGTH / config.DEFAULT_DEPTH:g} pixels/unit")
        explanation = "Depth does not change size. Screen Y points downward."
    else:
        formula = ("screen_x = cx + f*x/z", "screen_y = cy - f*y/z",
                   f"f = {config.FOCAL_LENGTH:g}; (cx, cy) = {config.CENTRE}")
        explanation = "Divide by camera depth: distant points appear smaller."
    if screen is None:
        explanation = ("Hidden or invalid point: no screen coordinate. Connected "
                       "edges may still be partly visible after clipping.")
    stages.append(PipelineStage("Projected screen coordinates", screen,
                                formula, explanation))
    return tuple(stages)
