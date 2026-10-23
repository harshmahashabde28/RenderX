"""Procedural geometric shape generators with parameter validation."""
from math import sin, cos, pi, isfinite, exp, hypot
from renderx.core.mesh import Mesh


def check(radius: float = 1, height: float = 2, segments: int = 12) -> None:
    """Validate procedural shape generator dimensional bounds."""
    if not all(isfinite(v) and 0 < v <= 100 for v in (radius, height)):
        raise ValueError("Dimensions must be finite, positive and at most 100.")
    if type(segments) is not int or not 3 <= segments <= 48:
        raise ValueError("Segments must be an integer from 3 to 48.")


def from_faces(vertices: list[tuple[float, float, float]], faces: list[list[int]]) -> Mesh:
    """Extract unique undirected boundary edges from a collection of polygonal faces."""
    edges = set()
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            edges.add(tuple(sorted((a, b))))
    return Mesh(vertices, sorted(edges), faces=faces)


def prism(radius: float = 1, height: float = 2, segments: int = 6, top_radius: float | None = None) -> Mesh:
    """Generate a regular prism or pyramid/cone with optional tapering."""
    check(radius, height, segments)
    top_radius = radius if top_radius is None else top_radius
    if not isfinite(top_radius) or not 0 <= top_radius <= 100:
        raise ValueError("Top radius must be from 0 to 100.")
    bottom = [
        (radius * cos(2 * pi * i / segments), -height / 2, radius * sin(2 * pi * i / segments))
        for i in range(segments)
    ]
    if top_radius == 0:
        vertices = bottom + [(0.0, height / 2, 0.0)]
        faces = [list(range(segments))] + [
            [i, (i + 1) % segments, segments] for i in range(segments)
        ]
    else:
        vertices = bottom + [
            (top_radius * cos(2 * pi * i / segments), height / 2, top_radius * sin(2 * pi * i / segments))
            for i in range(segments)
        ]
        faces = [list(range(segments)), list(range(segments, 2 * segments))]
        faces += [
            [i, (i + 1) % segments, (i + 1) % segments + segments, i + segments]
            for i in range(segments)
        ]
    return from_faces(vertices, faces)


def sphere(radius: float = 1, segments: int = 12, rings: int = 6) -> Mesh:
    """Generate a UV sphere mesh."""
    check(radius, 1, segments)
    if type(rings) is not int or not 2 <= rings <= 24:
        raise ValueError("Rings must be an integer from 2 to 24.")
    vertices = [(0.0, radius, 0.0)]
    for j in range(1, rings):
        a = pi * j / rings
        for i in range(segments):
            b = 2 * pi * i / segments
            vertices.append((radius * sin(a) * cos(b), radius * cos(a), radius * sin(a) * sin(b)))
    south = len(vertices)
    vertices.append((0.0, -radius, 0.0))
    faces = [[0, 1 + i, 1 + (i + 1) % segments] for i in range(segments)]
    for j in range(rings - 2):
        for i in range(segments):
            a = 1 + j * segments + i
            b = 1 + j * segments + (i + 1) % segments
            faces.append([a, b, b + segments, a + segments])
    faces += [
        [south, south - segments + i, south - segments + (i + 1) % segments]
        for i in range(segments)
    ]
    return from_faces(vertices, faces)


def torus(radius: float = 1, tube: float = 0.35, segments: int = 16, rings: int = 8) -> Mesh:
    """Generate a torus ring mesh."""
    check(radius, tube, segments)
    if tube >= radius or type(rings) is not int or not 3 <= rings <= 24:
        raise ValueError("Tube must be smaller than radius; rings must be 3 to 24.")
    vertices = []
    for i in range(segments):
        a = 2 * pi * i / segments
        for j in range(rings):
            b = 2 * pi * j / rings
            vertices.append(
                (
                    (radius + tube * cos(b)) * cos(a),
                    tube * sin(b),
                    (radius + tube * cos(b)) * sin(a),
                )
            )
    faces = []
    for i in range(segments):
        for j in range(rings):
            faces.append(
                [
                    i * rings + j,
                    ((i + 1) % segments) * rings + j,
                    ((i + 1) % segments) * rings + (j + 1) % rings,
                    i * rings + (j + 1) % rings,
                ]
            )
    return from_faces(vertices, faces)


def surface(kind: str = "Plane", width: float = 2, depth: float = 2, segments: int = 8) -> Mesh:
    """Generate a parametric height field surface: Plane, Saddle, or Ripple."""
    check(width, depth, segments)
    if kind not in ("Plane", "Saddle", "Ripple"):
        raise ValueError("Unknown surface kind.")
    vertices = []
    for j in range(segments + 1):
        z = depth * (j / segments - 0.5)
        for i in range(segments + 1):
            x = width * (i / segments - 0.5)
            if kind == "Plane":
                y = 0.0
            elif kind == "Saddle":
                y = (x * x - z * z) / 2.0
            else:
                y = 0.25 * cos(5.0 * (x * x + z * z) ** 0.5)
            vertices.append((x, y, z))
    faces = []
    for j in range(segments):
        for i in range(segments):
            a = j * (segments + 1) + i
            faces.append([a, a + 1, a + segments + 2, a + segments + 1])
    return from_faces(vertices, faces)


def helix(radius: float = 0.8, height: float = 2, segments: int = 36, turns: int = 3) -> Mesh:
    """Generate a 3D spiral helix curve."""
    check(radius, height, segments)
    if type(turns) is not int or not 1 <= turns <= 6:
        raise ValueError("Turns must be an integer from 1 to 6.")
    vertices = [
        (
            radius * cos(2 * pi * turns * i / segments),
            height * (i / segments - 0.5),
            radius * sin(2 * pi * turns * i / segments),
        )
        for i in range(segments + 1)
    ]
    return Mesh(vertices, [(i, i + 1) for i in range(segments)], faces=[])


def mobius_strip(radius: float = 0.75, width: float = 0.46, segments: int = 40, width_segments: int = 6) -> Mesh:
    """Create a triangulatable Möbius ribbon with its half-twist seam."""
    check(radius, width, segments)
    if type(width_segments) is not int or not 2 <= width_segments <= 16:
        raise ValueError("Width segments must be an integer from 2 to 16.")
    vertices = []
    for i in range(segments):
        angle = 2 * pi * i / segments
        for j in range(width_segments + 1):
            offset = width * (j / width_segments - 0.5)
            radial = radius + offset * cos(angle / 2)
            vertices.append(
                (
                    radial * cos(angle),
                    radial * sin(angle),
                    offset * sin(angle / 2),
                )
            )
    faces = []
    row = width_segments + 1
    for i in range(segments):
        next_i = (i + 1) % segments
        for j in range(width_segments):
            next_j = width_segments - j if next_i == 0 else j
            next_j1 = width_segments - j - 1 if next_i == 0 else j + 1
            faces.append([i * row + j, next_i * row + next_j, next_i * row + next_j1, i * row + j + 1])
    return from_faces(vertices, faces)


def signal_wave(segments: int = 18) -> Mesh:
    """A live height field whose surface is updated from its wave equation."""
    mesh = surface("Plane", width=3.2, depth=3.2, segments=segments)
    return update_signal_wave(mesh, 0.0)


def update_signal_wave(mesh: Mesh, phase: float, amplitude: float = 0.42) -> Mesh:
    """Re-evaluate a damped radial pulse crossed with a travelling wave."""
    mesh.vertices = [
        (
            x,
            amplitude * sin(4.2 * hypot(x, z) - phase * 2.2) * exp(-0.34 * hypot(x, z))
            + 0.12 * sin(2.8 * x + phase) * cos(2.8 * z - phase * 0.72),
            z,
        )
        for x, _, z in mesh.vertices
    ]
    return mesh


def extra_models() -> dict[str, Mesh]:
    """Library of extra procedural polyhedra and curved surfaces."""
    tetra = from_faces(
        [(1, 1, 1), (-1, -1, 1), (-1, 1, -1), (1, -1, -1)],
        [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
    )
    octa = from_faces(
        [(1, 0, 0), (0, 0, 1), (-1, 0, 0), (0, 0, -1), (0, 1, 0), (0, -1, 0)],
        [[pole, i, (i + 1) % 4] for pole in (4, 5) for i in range(4)],
    )
    return {
        "Tetrahedron": tetra,
        "Octahedron": octa,
        "Triangular prism": prism(segments=3),
        "Hexagonal prism": prism(),
        "Cylinder": prism(segments=12),
        "Cone": prism(segments=12, top_radius=0),
        "Sphere": sphere(),
        "Torus": torus(),
        "Plane": surface(),
        "Saddle": surface("Saddle"),
        "Ripple": surface("Ripple"),
        "Helix": helix(),
        "Möbius ribbon": mobius_strip(),
        "Signal wave": signal_wave(),
    }
