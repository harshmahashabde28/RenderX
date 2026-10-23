"""Render style definitions and visual configuration for the software renderer."""
from enum import Enum
from dataclasses import dataclass
from typing import Tuple

Color = Tuple[int, int, int]


class RenderStyle(str, Enum):
    WIREFRAME = "Wireframe"
    VERTICES = "Wireframe + vertices"
    DEPTH_FADE = "Depth-fade"
    SOLID = "Solid"
    XRAY = "X-ray"

    @classmethod
    def all_styles(cls) -> list[str]:
        return [s.value for s in cls]


@dataclass
class StyleConfig:
    style: RenderStyle = RenderStyle.WIREFRAME
    vertex_radius: int = 3
    fade_start_depth: float = 3.0
    fade_end_depth: float = 25.0
    xray_dim_factor: float = 0.28
    light_direction: Tuple[float, float, float] = (0.577, 0.577, -0.577)  # Normalized (1, 1, -1)
