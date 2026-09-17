"""Pure 3D maths. X right, Y up, positive Z away from the viewer."""
from math import cos, sin


def rotate_x(point, angle):
    x, y, z = point
    c, s = cos(angle), sin(angle)
    return x, y * c - z * s, y * s + z * c


def rotate_y(point, angle):
    x, y, z = point
    c, s = cos(angle), sin(angle)
    return x * c + z * s, y, -x * s + z * c


def rotate_z(point, angle):
    x, y, z = point
    c, s = cos(angle), sin(angle)
    return x * c - y * s, x * s + y * c, z


def transform_vertex(point, scene):
    # Scale and rotate around the model origin BEFORE positioning in the world.
    point = tuple(value * scene.scale for value in point)
    point = rotate_x(point, scene.angles[0])
    point = rotate_y(point, scene.angles[1])
    point = rotate_z(point, scene.angles[2])
    return tuple(value + offset for value, offset in zip(point, scene.position))
