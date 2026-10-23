"""Small eased transitions for hovered and pressed UI controls."""

from __future__ import annotations

from .theme import METRICS


class Animator:
    def __init__(self):
        self.values: dict[object, float] = {}

    def value(self, key, target: float, dt: float) -> float:
        current = self.values.get(key, target)
        rate = min(1.0, max(0.0, dt) * 1000 / METRICS["transition_ms"])
        eased = 1.0 - (1.0 - rate) * (1.0 - rate)
        current += (target - current) * eased
        if abs(target - current) < 0.01:
            current = target
        self.values[key] = current
        return current

    def clear(self):
        self.values.clear()
