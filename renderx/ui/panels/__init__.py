"""Mode-specific dock contents for the RenderX editor shell."""

from .challenge import draw_challenge_panel
from .inspector import draw_inspector_panel
from .maze import draw_maze_panel
from .scene import ScenePanel
from .shooter import draw_shooter_panel

__all__ = [
    "ScenePanel", "draw_inspector_panel", "draw_challenge_panel",
    "draw_maze_panel", "draw_shooter_panel",
]
