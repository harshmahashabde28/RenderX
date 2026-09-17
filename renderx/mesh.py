"""A mesh is just vertices and pairs of vertex indices (edges)."""
from dataclasses import dataclass
from math import isfinite


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]]
    edges: list[tuple[int, int]]

    def __post_init__(self):
        validate_mesh(self)


def validate_mesh(mesh):
    if not mesh.vertices:
        raise ValueError("A mesh must have vertices.")
    for point in mesh.vertices:
        if len(point) != 3 or not all(isfinite(value) for value in point):
            raise ValueError(f"Invalid 3D vertex: {point}")
    seen = set()
    for edge in mesh.edges:
        if len(edge) != 2 or not all(
            type(index) is int and 0 <= index < len(mesh.vertices)
            for index in edge
        ):
            raise ValueError(f"Invalid edge indices: {edge}")
        if edge[0] == edge[1] or tuple(sorted(edge)) in seen:
            raise ValueError(f"Self-connected or duplicate edge: {edge}")
        seen.add(tuple(sorted(edge)))
