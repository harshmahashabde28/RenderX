"""Compatibility wrapper for renderx.engine.renderer."""
from renderx.engine.renderer import (
    VIEWPORT,
    draw_wireframe,
    draw_selected_vertex,
    _draw_visible_edge,
)

__all__ = [
    "VIEWPORT",
    "draw_wireframe",
    "draw_selected_vertex",
    "_draw_visible_edge",
]
