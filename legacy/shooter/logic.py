"""Small, testable rules shared by the 3D shooter runtime."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Difficulty:
    name: str
    enemy_health: int
    enemy_speed: float
    enemy_fire_interval: float
    player_damage: float
    starting_health: int = 100


DIFFICULTIES = {
    "EASY": Difficulty("EASY", 2, 2.35, 2.2, 7.0),
    "NORMAL": Difficulty("NORMAL", 3, 2.8, 1.75, 9.0),
    "HARD": Difficulty("HARD", 4, 3.2, 1.35, 12.0),
}


def enemy_count_for_wave(wave: int) -> int:
    """Return a paced, steadily increasing enemy count for a wave."""
    return max(0, 3 + (max(1, int(wave)) - 1) * 2)


def aabb_overlap(x1, z1, w1, d1, x2, z2, w2, d2) -> bool:
    """Return whether two axis-aligned ground-plane boxes overlap."""
    return abs(x1 - x2) < (w1 + w2) / 2 and abs(z1 - z2) < (d1 + d2) / 2


def clamp_frame_time(delta_time: float, maximum: float = 0.05) -> float:
    """Avoid simulation jumps after a breakpoint, focus loss, or resize."""
    return min(max(0.0, float(delta_time)), maximum)
