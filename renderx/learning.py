"""Small learning state; independent of Pygame and the scene's object pose."""
from dataclasses import dataclass

MODES = ("Explore", "Pipeline")
STAGE_COUNT = 8


@dataclass
class LearningState:
    mode: str = "Explore"
    selected_vertex: int = 0
    stage_index: int = 0

    def cycle_mode(self):
        self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]

    def select_vertex(self, step, vertex_count):
        """Wrap at either end; empty meshes have no selectable vertex."""
        if vertex_count <= 0:
            self.selected_vertex = 0
        else:
            self.selected_vertex = (self.selected_vertex + step) % vertex_count

    def select_stage(self, step):
        self.stage_index = (self.stage_index + step) % STAGE_COUNT
