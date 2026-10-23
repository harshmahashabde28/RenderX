"""Compatibility wrapper for renderx.core.obj_loader."""
from renderx.core.obj_loader import (
    SAMPLE_OBJ,
    MAX_FILE_BYTES,
    MAX_VERTICES,
    MAX_EDGES,
    normalize_vertices,
    load_obj,
)

__all__ = [
    "SAMPLE_OBJ",
    "MAX_FILE_BYTES",
    "MAX_VERTICES",
    "MAX_EDGES",
    "normalize_vertices",
    "load_obj",
]
