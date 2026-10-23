"""Fixed-timestep simulation loop and frame timing manager."""
from typing import Callable
from renderx import config

MAX_FRAME_DELTA = 0.05
FIXED_TIMESTEP = 1.0 / 60.0


class TimeStepLoop:
    """Manages fixed-interval physics ticks decoupled from variable rendering framerate."""

    def __init__(self, fixed_dt: float = FIXED_TIMESTEP, max_dt: float = MAX_FRAME_DELTA):
        self.fixed_dt = fixed_dt
        self.max_dt = max_dt
        self.accumulator = 0.0
        self.frame_count = 0
        self.elapsed_time = 0.0

    def step(self, raw_dt: float, update_fn: Callable[[float], None]) -> int:
        """Accumulate delta time and invoke update_fn at fixed dt intervals.

        Returns number of physics ticks processed.
        """
        clamped_dt = min(max(raw_dt, 0.0), self.max_dt)
        self.accumulator += clamped_dt
        self.elapsed_time += clamped_dt

        ticks = 0
        while self.accumulator >= self.fixed_dt:
            update_fn(self.fixed_dt)
            self.accumulator -= self.fixed_dt
            ticks += 1
            if ticks >= 5:  # Prevent spiral of death on severe lag
                self.accumulator = 0.0
                break

        self.frame_count += 1
        return ticks
