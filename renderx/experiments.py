"""Pure experiment maths; diagrams use these exact results."""
from renderx.clipping import clip_edge_near
from renderx.transform import transform_vertex, rotate_x, rotate_y, rotate_z
from renderx import config


def clipping_experiment(depth):
    a, b = (-1, 0, depth-.7), (1, 0, depth+.7)
    clipped = clip_edge_near(a, b)
    state = "hidden" if clipped is None else ("complete" if clipped == (a,b) else "partial")
    t = None if state != "partial" else (config.NEAR_DEPTH-a[2])/(b[2]-a[2])
    return a, b, clipped, state, t


def order_experiment(point, scene):
    normal = transform_vertex(point, scene)
    moved = tuple(v+t for v,t in zip(point, scene.position))
    rotated = rotate_z(rotate_y(rotate_x(moved, scene.angles[0]), scene.angles[1]), scene.angles[2])
    alternative = tuple(v*scene.scale for v in rotated)
    return normal, alternative
