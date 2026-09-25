"""A mesh is just vertices and pairs of vertex indices (edges)."""
from dataclasses import dataclass, field
from math import isfinite


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]]
    edges: list[tuple[int, int]]

    faces: list | None = None
    normalization_scale: float | None = 1.0
    warnings: list[str] = field(default_factory=list)

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

    if mesh.faces is not None:
        for face in mesh.faces:
            if len(face) < 3 or len(set(face)) != len(face) or not all(
                    type(i) is int and 0 <= i < len(mesh.vertices) for i in face):
                raise ValueError("Invalid face indices.")


def inspect_mesh(mesh):
    """Report diagnostics without altering geometry (including malformed edges)."""
    low = tuple(min(p[a] for p in mesh.vertices) for a in range(3))
    high = tuple(max(p[a] for p in mesh.vertices) for a in range(3))
    seen, connected = set(), set()
    duplicates = invalid = 0
    for edge in mesh.edges:
        if len(edge) != 2 or not all(type(i) is int and 0 <= i < len(mesh.vertices) for i in edge):
            invalid += 1
            continue
        canonical = tuple(sorted(edge))
        duplicates += canonical in seen
        seen.add(canonical)
        connected.update(edge)
    return {"vertices": len(mesh.vertices), "edges": len(mesh.edges),
            "faces": None if mesh.faces is None else len(mesh.faces),
            "low": low, "high": high,
            "center": tuple(a/2+b/2 for a,b in zip(low,high)),
            "size": tuple(b-a for a,b in zip(low,high)),
            "normalization_scale": mesh.normalization_scale,
            "duplicate_edges": duplicates, "invalid_edges": invalid,
            "disconnected": len(mesh.vertices)-len(connected),
            "warnings": list(mesh.warnings)}
