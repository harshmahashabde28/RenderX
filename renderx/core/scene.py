"""Scene state management for model orientation, translation, scale, and projection."""
from dataclasses import dataclass
from math import tau
from typing import Tuple
from renderx import config

Point3D = Tuple[float, float, float]


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


@dataclass
class Scene:
    """Configurable scene parameters governing the active model in the viewport."""
    shape: str = "Cube"
    angles: Point3D = config.DEFAULT_ANGLES
    position: Point3D = (0.0, 0.0, config.DEFAULT_DEPTH)
    scale: float = 1.0
    projection: str = "Perspective"
    axes_visible: bool = True

    def rotate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> None:
        """Increment scene rotation angles modulo 2pi."""
        self.angles = tuple(
            (angle + change) % tau for angle, change in zip(self.angles, (dx, dy, dz))
        )  # type: ignore

    def move(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> None:
        """Translate model position within safe world bounds."""
        x, y, z = self.position
        limit = config.POSITION_LIMIT
        self.position = (
            clamp(x + dx, -limit, limit),
            clamp(y + dy, -limit, limit),
            clamp(z + dz, config.MIN_DEPTH, config.MAX_DEPTH),
        )

    def resize(self, amount: float) -> None:
        """Adjust uniform scale within configured minimum and maximum bounds."""
        self.scale = clamp(self.scale + amount, config.MIN_SCALE, config.MAX_SCALE)

    def reset(self) -> None:
        """Reset orientation, position, and scale back to defaults."""
        self.angles = config.DEFAULT_ANGLES
        self.position = (0.0, 0.0, config.DEFAULT_DEPTH)
        self.scale = 1.0

    def select(self, name: str) -> None:
        """Select a new mesh shape from the model library and reset pose."""
        self.shape = name
        self.reset()
