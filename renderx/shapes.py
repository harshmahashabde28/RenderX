"""Small procedural meshes: explicit loops, low detail, standard maths only."""
from math import sin, cos, pi, isfinite
from renderx.mesh import Mesh


def check(radius=1, height=2, segments=12):
    if not all(isfinite(v) and 0 < v <= 100 for v in (radius, height)):
        raise ValueError("Dimensions must be finite, positive and at most 100.")
    if type(segments) is not int or not 3 <= segments <= 48:
        raise ValueError("Segments must be an integer from 3 to 48.")


def from_faces(vertices, faces):
    edges = set()
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            edges.add(tuple(sorted((a, b))))
    return Mesh(vertices, sorted(edges), faces=faces)


def prism(radius=1, height=2, segments=6, top_radius=None):
    check(radius, height, segments)
    top_radius = radius if top_radius is None else top_radius
    if not isfinite(top_radius) or not 0 <= top_radius <= 100:
        raise ValueError("Top radius must be from 0 to 100.")
    bottom = [(radius*cos(2*pi*i/segments), -height/2,
               radius*sin(2*pi*i/segments)) for i in range(segments)]
    if top_radius == 0:
        vertices = bottom + [(0, height/2, 0)]
        faces = [list(range(segments))] + [[i, (i+1)%segments, segments]
                                          for i in range(segments)]
    else:
        vertices = bottom + [(top_radius*cos(2*pi*i/segments), height/2,
                               top_radius*sin(2*pi*i/segments)) for i in range(segments)]
        faces = [list(range(segments)), list(range(segments, 2*segments))]
        faces += [[i, (i+1)%segments, (i+1)%segments+segments, i+segments]
                  for i in range(segments)]
    return from_faces(vertices, faces)


def sphere(radius=1, segments=12, rings=6):
    check(radius, 1, segments)
    if type(rings) is not int or not 2 <= rings <= 24:
        raise ValueError("Rings must be an integer from 2 to 24.")
    vertices = [(0, radius, 0)]
    for j in range(1, rings):
        a = pi*j/rings
        for i in range(segments):
            b = 2*pi*i/segments
            vertices.append((radius*sin(a)*cos(b), radius*cos(a), radius*sin(a)*sin(b)))
    south = len(vertices)
    vertices.append((0, -radius, 0))
    faces = [[0, 1+i, 1+(i+1)%segments] for i in range(segments)]
    for j in range(rings-2):
        for i in range(segments):
            a = 1+j*segments+i; b = 1+j*segments+(i+1)%segments
            faces.append([a, b, b+segments, a+segments])
    faces += [[south, south-segments+i, south-segments+(i+1)%segments]
              for i in range(segments)]
    return from_faces(vertices, faces)


def torus(radius=1, tube=.35, segments=16, rings=8):
    check(radius, tube, segments)
    if tube >= radius or type(rings) is not int or not 3 <= rings <= 24:
        raise ValueError("Tube must be smaller than radius; rings must be 3 to 24.")
    vertices = []
    for i in range(segments):
        a = 2*pi*i/segments
        for j in range(rings):
            b = 2*pi*j/rings
            vertices.append(((radius+tube*cos(b))*cos(a), tube*sin(b),
                             (radius+tube*cos(b))*sin(a)))
    faces = []
    for i in range(segments):
        for j in range(rings):
            faces.append([i*rings+j, ((i+1)%segments)*rings+j,
                          ((i+1)%segments)*rings+(j+1)%rings, i*rings+(j+1)%rings])
    return from_faces(vertices, faces)


def surface(kind="Plane", width=2, depth=2, segments=8):
    check(width, depth, segments)
    if kind not in ("Plane", "Saddle", "Ripple"):
        raise ValueError("Unknown surface kind.")
    vertices = []
    for j in range(segments+1):
        z = depth*(j/segments-.5)
        for i in range(segments+1):
            x = width*(i/segments-.5)
            y = 0 if kind == "Plane" else ((x*x-z*z)/2 if kind == "Saddle"
                                         else .25*cos(5*(x*x+z*z)**.5))
            vertices.append((x, y, z))
    faces = []
    for j in range(segments):
        for i in range(segments):
            a = j*(segments+1)+i
            faces.append([a, a+1, a+segments+2, a+segments+1])
    return from_faces(vertices, faces)


def helix(radius=.8, height=2, segments=36, turns=3):
    check(radius, height, segments)
    if type(turns) is not int or not 1 <= turns <= 6:
        raise ValueError("Turns must be an integer from 1 to 6.")
    vertices = [(radius*cos(2*pi*turns*i/segments), height*(i/segments-.5),
                 radius*sin(2*pi*turns*i/segments)) for i in range(segments+1)]
    return Mesh(vertices, [(i, i+1) for i in range(segments)], faces=[])


def extra_models():
    tetra = from_faces([(1,1,1), (-1,-1,1), (-1,1,-1), (1,-1,-1)],
                       [[0,1,2], [0,1,3], [0,2,3], [1,2,3]])
    octa = from_faces([(1,0,0), (0,0,1), (-1,0,0), (0,0,-1), (0,1,0), (0,-1,0)],
                      [[pole,i,(i+1)%4] for pole in (4,5) for i in range(4)])
    return {"Tetrahedron": tetra, "Octahedron": octa,
            "Triangular prism": prism(segments=3), "Hexagonal prism": prism(),
            "Cylinder": prism(segments=12), "Cone": prism(segments=12, top_radius=0),
            "Sphere": sphere(), "Torus": torus(), "Plane": surface(),
            "Saddle": surface("Saddle"), "Ripple": surface("Ripple"), "Helix": helix()}
