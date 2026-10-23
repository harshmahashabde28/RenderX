"""Compatibility wrapper for renderx.core.clipping."""
from renderx.core.clipping import (
    clip_edge_near,
    clip_line_2d_liang_barsky,
    clip_line_2d_cohen_sutherland,
)

__all__ = [
    "clip_edge_near",
    "clip_line_2d_liang_barsky",
    "clip_line_2d_cohen_sutherland",
]
