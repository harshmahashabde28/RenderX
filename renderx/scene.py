"""Shared scene actions used by BOTH keyboard and mouse."""
from dataclasses import dataclass
from math import tau
from renderx import config


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


@dataclass
class Scene:
    # A dataclass groups these values and supplies an initialiser for us.
    shape: str = "Cube"
    angles: tuple = config.DEFAULT_ANGLES
    position: tuple = (0.0, 0.0, config.DEFAULT_DEPTH)
    scale: float = 1.0
    projection: str = "Perspective"
    axes_visible: bool = True

    def rotate(self, dx=0.0, dy=0.0, dz=0.0):
        self.angles = tuple((angle + change) % tau for angle, change
                            in zip(self.angles, (dx, dy, dz)))

    def move(self, dx=0.0, dy=0.0, dz=0.0):
        x, y, z = self.position
        limit = config.POSITION_LIMIT
        self.position = (clamp(x + dx, -limit, limit),
                         clamp(y + dy, -limit, limit),
                         clamp(z + dz, config.MIN_DEPTH, config.MAX_DEPTH))

    def resize(self, amount):
        self.scale = clamp(self.scale + amount,
                           config.MIN_SCALE, config.MAX_SCALE)

    def reset(self):
        self.angles = config.DEFAULT_ANGLES
        self.position = (0.0, 0.0, config.DEFAULT_DEPTH)
        self.scale = 1.0

    def select(self, name):
        self.shape = name
        self.reset()
