"""Shared software-rendering utilities used by the workspace and maze."""
from renderx.engine.renderer import (
    VIEWPORT,
    draw_wireframe,
    draw_selected_vertex,
)
from renderx.engine.styles import RenderStyle, StyleConfig
from renderx.engine.culling import (
    is_within_distance,
    calculate_face_normal,
    is_backface,
)
from renderx.engine.spatial import SpatialGrid
from renderx.engine.fast_math import (
    has_numpy,
    batch_transform,
    batch_transform_pure,
    batch_transform_numpy,
)
from renderx.engine.axes import draw_axes

__all__ = [
    "VIEWPORT",
    "draw_wireframe",
    "draw_selected_vertex",
    "RenderStyle",
    "StyleConfig",
    "is_within_distance",
    "calculate_face_normal",
    "is_backface",
    "SpatialGrid",
    "has_numpy",
    "batch_transform",
    "batch_transform_pure",
    "batch_transform_numpy",
    "draw_axes",
]
