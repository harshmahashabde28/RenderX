"""RenderX Core: Pure Python 3D mathematics, meshes, and geometric transforms.

This package contains no Pygame, engine, UI, or platform-specific dependencies.
"""
from renderx.core.vec import Vec3
from renderx.core.mesh import Mesh, inspect_mesh, validate_mesh
from renderx.core.transform import (
    rotate_x,
    rotate_y,
    rotate_z,
    transform_vertex,
    transform_stages,
)
from renderx.core.clipping import (
    clip_edge_near,
    clip_line_2d_liang_barsky,
    clip_line_2d_cohen_sutherland,
)
from renderx.core.projection import (
    project_point,
    project_perspective,
    project_orthographic,
)
from renderx.core.camera import Camera
from renderx.core.scene import Scene
from renderx.core.models import make_models, make_library, make_cube, make_pyramid, make_prism
from renderx.core.shapes import extra_models
from renderx.core.obj_loader import load_obj, SAMPLE_OBJ

__all__ = [
    "Vec3",
    "Mesh",
    "inspect_mesh",
    "validate_mesh",
    "rotate_x",
    "rotate_y",
    "rotate_z",
    "transform_vertex",
    "transform_stages",
    "clip_edge_near",
    "clip_line_2d_liang_barsky",
    "clip_line_2d_cohen_sutherland",
    "project_point",
    "project_perspective",
    "project_orthographic",
    "Camera",
    "Scene",
    "make_models",
    "make_library",
    "make_cube",
    "make_pyramid",
    "make_prism",
    "extra_models",
    "load_obj",
    "SAMPLE_OBJ",
]
