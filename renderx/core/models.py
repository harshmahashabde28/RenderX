"""Built-in geometric mesh primitives and full library initialization."""
from renderx.core.mesh import Mesh


def make_cube() -> Mesh:
    """Standard unit cube with edge length 2 centered at the origin."""
    vertices = [
        (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), (-1.0, 1.0, -1.0),
        (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # Front square
        (4, 5), (5, 6), (6, 7), (7, 4),  # Back square
        (0, 4), (1, 5), (2, 6), (3, 7),  # Connect the squares
    ]
    faces = [
        [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
        [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]
    ]
    return Mesh(vertices, edges, faces=faces)


def make_pyramid() -> Mesh:
    """Square-based pyramid pointing along positive Y."""
    vertices = [
        (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, -1.0, 1.0), (-1.0, -1.0, 1.0),
        (0.0, 1.0, 0.0),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (0, 4), (1, 4), (2, 4), (3, 4),
    ]
    faces = [
        [0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]
    ]
    return Mesh(vertices, edges, faces=faces)


def make_prism() -> Mesh:
    """Rectangular cuboid prism scaled along axes."""
    cube = make_cube()
    vertices = [(x * 1.4, y * 0.7, z * 0.8) for x, y, z in cube.vertices]
    faces = [face.copy() for face in cube.faces] if cube.faces else None
    return Mesh(vertices, cube.edges.copy(), faces=faces)


def make_models() -> dict[str, Mesh]:
    """Base standard primitive model catalog."""
    return {
        "Cube": make_cube(),
        "Pyramid": make_pyramid(),
        "Rectangular prism": make_prism(),
    }


def make_library() -> dict[str, Mesh]:
    """Complete collection of all 17 procedural built-in shapes."""
    from renderx.core.shapes import extra_models
    models = make_models()
    models.update(extra_models())
    return models
