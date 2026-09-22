"""Read a small OBJ subset and turn polygon boundaries into unique edges."""
from math import isfinite
from pathlib import Path
from renderx.mesh import Mesh

SAMPLE_OBJ = Path(__file__).resolve().parent.parent / "assets/models/house.obj"
MAX_FILE_BYTES = 2_000_000
MAX_VERTICES = 20_000
MAX_EDGES = 50_000


def normalize_vertices(vertices):
    """Centre the bounding box and make its longest side two world units."""
    # Reduce large finite coordinates first so bounding-box arithmetic is safe.
    largest = max(abs(value) for point in vertices for value in point)
    if largest == 0:
        raise ValueError("Model has no spatial extent.")
    points = [tuple(value / largest for value in point) for point in vertices]
    low = [min(point[axis] for point in points) for axis in range(3)]
    high = [max(point[axis] for point in points) for axis in range(3)]
    extent = max(high[axis] - low[axis] for axis in range(3))
    if extent == 0:
        raise ValueError("Model has no spatial extent.")
    centre = [(a + b) / 2 for a, b in zip(low, high)]
    return [tuple((value - centre[axis]) / extent * 2
                  for axis, value in enumerate(point)) for point in points]


def load_obj(path):
    """Raise a readable ValueError/OSError; caller keeps the current model."""
    with Path(path).open("r", encoding="utf-8-sig") as source:
        text = source.read(MAX_FILE_BYTES + 1)
    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("OBJ exceeds the 2 MB educational loader limit.")
    vertices, faces = [], []
    for line_number, line in enumerate(text.splitlines(), 1):
        fields = line.split("#", 1)[0].split()
        if not fields:
            continue
        try:
            if fields[0] == "v":
                if len(fields) != 4:
                    raise ValueError("vertices must contain exactly x y z")
                point = tuple(float(value) for value in fields[1:])
                if not all(isfinite(value) for value in point):
                    raise ValueError("vertex coordinates must be finite")
                vertices.append(point)
                if len(vertices) > MAX_VERTICES:
                    raise ValueError("too many vertices (limit 20000)")
            elif fields[0] == "f":
                face = []
                for entry in fields[1:]:
                    parts = entry.split("/")
                    if (len(parts) > 3 or not parts[0]
                            or (len(parts) == 2 and not parts[1])
                            or (len(parts) == 3 and not parts[2])):
                        raise ValueError("unsupported face entry")
                    index = int(parts[0])
                    if index <= 0:
                        raise ValueError("only positive vertex indices supported")
                    # Check token syntax, but do not load texture/normal data.
                    for suffix in parts[1:]:
                        if suffix:
                            int(suffix)
                    face.append(index - 1)  # OBJ starts at 1, Python at 0.
                if len(face) < 3 or len(set(face)) != len(face):
                    raise ValueError("face needs at least 3 distinct vertices")
                faces.append((line_number, face))
            # vt, vn, materials, groups and all other commands are ignored.
        except ValueError as error:
            raise ValueError(f"OBJ line {line_number}: {error}") from error
    if not vertices or not faces:
        raise ValueError("OBJ needs vertices and at least one polygon face.")
    edges = set()
    for line_number, face in faces:
        if any(index >= len(vertices) for index in face):
            raise ValueError(f"OBJ line {line_number}: vertex index out of range")
        for start, end in zip(face, face[1:] + face[:1]):
            edges.add(tuple(sorted((start, end))))
            if len(edges) > MAX_EDGES:
                raise ValueError("Too many unique edges (limit 50000).")
    return Mesh(normalize_vertices(vertices), sorted(edges))
