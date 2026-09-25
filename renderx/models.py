"""Original geometry stays unchanged while a scene is manipulated."""
from renderx.mesh import Mesh


def make_cube():
    vertices = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # Front square
        (4, 5), (5, 6), (6, 7), (7, 4),  # Back square
        (0, 4), (1, 5), (2, 6), (3, 7),  # Connect the squares
    ]
    return Mesh(vertices, edges, faces=[[0,1,2,3], [4,5,6,7], [0,1,5,4],
                                       [1,2,6,5], [2,3,7,6], [3,0,4,7]])


def make_pyramid():
    return Mesh(
        [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1),
         (0, 1, 0)],
        [(0, 1), (1, 2), (2, 3), (3, 0),
         (0, 4), (1, 4), (2, 4), (3, 4)],
        faces=[[0,1,2,3], [0,1,4], [1,2,4], [2,3,4], [3,0,4]],
    )


def make_prism():
    cube = make_cube()
    return Mesh([(x * 1.4, y * 0.7, z * 0.8) for x, y, z in cube.vertices],
                cube.edges.copy(), faces=[face.copy() for face in cube.faces])


def make_models():
    return {"Cube": make_cube(), "Pyramid": make_pyramid(),
            "Rectangular prism": make_prism()}


def make_library():
    from renderx.shapes import extra_models
    models = make_models()
    models.update(extra_models())
    return models
