"""Deterministic Projection Quest content and small state machine."""
from dataclasses import dataclass
from math import pi, radians, tau

from renderx import config
from renderx.clipping import clip_edge_near
from renderx.scene import Scene
from renderx.transform import transform_vertex

MATCH_THRESHOLD = radians(15)
DEPTH_TEST_DISTANCE = 0.35


@dataclass(frozen=True)
class ChallengeDef:
    title: str
    kind: str
    setup_shape: str
    setup_projection: str
    setup_depth: float
    allowed_controls: tuple[str, ...]
    use_comparison: bool
    target_angles: tuple | None
    question: str
    choices: tuple[str, ...] | None
    correct: int | None
    explanation: str
    task: str
    start_angles: tuple | None = None


CHALLENGES = (
    ChallengeDef(
        title="Shape Match", kind="align", setup_shape="Pyramid",
        setup_projection="Perspective", setup_depth=5.0,
        allowed_controls=("rotate",), use_comparison=False,
        target_angles=config.DEFAULT_ANGLES,
        question="Rotate the wireframe until it matches the target view.",
        choices=None, correct=None,
        explanation="A wireframe is vertices and edges. Rotating it reveals the same shape from another viewpoint.",
        task="Match the target orientation.",
        start_angles=(radians(73), radians(142), radians(38)),
    ),
    ChallengeDef(
        title="Depth and Projection", kind="choice", setup_shape="Cube",
        setup_projection="Perspective", setup_depth=5.0,
        allowed_controls=("depth",), use_comparison=True,
        target_angles=config.DEFAULT_ANGLES,
        question="Move the cube farther away. In which view does it get smaller?",
        choices=("Left — Perspective", "Right — Orthographic", "Both views"),
        correct=0,
        explanation=("Perspective divides by depth, so distant objects look smaller. "
                     "Orthographic keeps a fixed scale, which is useful for engineering drawings."),
        task="Watch both views as the cube moves farther away.",
    ),
    ChallengeDef(
        title="Clipping Rescue", kind="choice_gated", setup_shape="Cube",
        setup_projection="Perspective", setup_depth=3.0,
        allowed_controls=("depth",), use_comparison=False,
        target_angles=config.DEFAULT_ANGLES,
        question="Why did some edges disappear?",
        choices=("They crossed the near plane", "They became too small to draw",
                 "The renderer removed them by mistake"),
        correct=0,
        explanation=("Edges crossing the near plane are shortened to their visible part. "
                     "Edges fully behind it are hidden before projection, avoiding division by zero."),
        task="Move the cube toward you until part of it reaches the near plane.",
    ),
)


def angle_diff(a, b):
    """Return the shortest unsigned angular distance in radians."""
    distance = (a - b) % tau
    return min(distance, tau - distance)


def is_aligned(current_angles, target_angles, threshold=MATCH_THRESHOLD):
    """Whether all three wrapped angle differences fit within the tolerance."""
    if len(current_angles) != 3 or len(target_angles) != 3:
        return False
    return all(angle_diff(current, target) <= threshold
               for current, target in zip(current_angles, target_angles))


def alignment_progress(current_angles, target_angles):
    """Return a 0..1 proximity value based on the largest axis difference."""
    if len(current_angles) != 3 or len(target_angles) != 3:
        return 0.0
    largest_error = max(angle_diff(current, target)
                        for current, target in zip(current_angles, target_angles))
    return max(0.0, min(1.0, 1.0 - largest_error / pi))


def make_challenge_scene(challenge):
    """Create a fresh scene for a quest step without altering the Explore scene."""
    return Scene(
        shape=challenge.setup_shape,
        angles=challenge.start_angles or challenge.target_angles or config.DEFAULT_ANGLES,
        position=(0.0, 0.0, challenge.setup_depth),
        scale=1.0,
        projection=challenge.setup_projection,
        axes_visible=True,
    )


def clipped_edge_count(mesh, scene, camera):
    """Count mesh edges shortened by the renderer's actual near-plane clipper."""
    world_points = [transform_vertex(vertex, scene) for vertex in mesh.vertices]
    clipped_count = 0
    for start, end in mesh.edges:
        world_a, world_b = world_points[start], world_points[end]
        camera_a, camera_b = camera.relative_point(world_a), camera.relative_point(world_b)
        visible = clip_edge_near(camera_a, camera_b)
        if visible is not None and visible != (camera_a, camera_b):
            clipped_count += 1
    return clipped_count


@dataclass
class QuestState:
    """In-memory progress; it is created once and survives tab switches."""
    current: int = 0
    answer: int | None = None
    confirmed: bool = False
    attempts: int = 0
    last_answer_correct: bool | None = None
    depth_tested: bool = False
    clipping_seen: bool = False

    @property
    def done(self):
        return self.current >= len(CHALLENGES)

    @property
    def challenge(self):
        return None if self.done else CHALLENGES[self.current]

    def select_answer(self, answer):
        challenge = self.challenge
        if (challenge is None or challenge.choices is None or self.confirmed or
                type(answer) is not int or not 0 <= answer < len(challenge.choices)):
            return False
        if challenge.kind == "choice_gated" and not self.clipping_seen:
            return False
        if challenge.title == "Depth and Projection" and not self.depth_tested:
            return False
        self.answer = answer
        self.last_answer_correct = None
        return True

    def check_answer(self):
        challenge = self.challenge
        if (challenge is None or challenge.choices is None or self.answer is None or
                self.confirmed):
            return False
        self.attempts += 1
        self.last_answer_correct = self.answer == challenge.correct
        self.confirmed = self.last_answer_correct
        return self.confirmed

    def observe_depth(self, depth):
        challenge = self.challenge
        if (challenge is not None and challenge.title == "Depth and Projection" and
                depth >= challenge.setup_depth + DEPTH_TEST_DISTANCE):
            self.depth_tested = True

    def observe_clipping(self, count):
        if self.challenge is not None and self.challenge.kind == "choice_gated" and count > 0:
            self.clipping_seen = True

    def observe_alignment(self, angles):
        challenge = self.challenge
        if (challenge is not None and challenge.kind == "align" and
                is_aligned(angles, challenge.target_angles)):
            self.confirmed = True

    def advance(self):
        """Advance only after this challenge has been solved."""
        if self.done or not self.confirmed:
            return False
        self.current += 1
        self.answer = None
        self.confirmed = False
        self.attempts = 0
        self.last_answer_correct = None
        self.depth_tested = False
        self.clipping_seen = False
        return True
