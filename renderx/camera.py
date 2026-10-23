"""Compatibility wrapper for renderx.core.camera and projection."""
from renderx.core.camera import Camera
from renderx.core.projection import project_point, project_perspective, project_orthographic

__all__ = [
    "Camera",
    "project_point",
    "project_perspective",
    "project_orthographic",
]
