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


def transform_stages(point, scene):
    """Return each step, so rendering and the inspector use identical maths."""
    original = tuple(point)
    scaled = tuple(value * scene.scale for value in original)
    x_rotated = rotate_x(scaled, scene.angles[0])
    y_rotated = rotate_y(x_rotated, scene.angles[1])
    z_rotated = rotate_z(y_rotated, scene.angles[2])
    translated = tuple(value + offset for value, offset
                       in zip(z_rotated, scene.position))
    return original, scaled, x_rotated, y_rotated, z_rotated, translated


def transform_vertex(point, scene):
    # Scale and rotate around the model origin BEFORE positioning in the world.
    return transform_stages(point, scene)[-1]
