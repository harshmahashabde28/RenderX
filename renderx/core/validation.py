"""Validation utilities for geometric coordinates, boundaries, and models."""
from math import isfinite
from typing import Sequence, Any


def check_finite(values: Sequence[float], name: str = "Values") -> None:
    for val in values:
        if not isfinite(val):
            raise ValueError(f"{name} must be finite real numbers. Got {val}")


def clamp_val(val: float, low: float, high: float) -> float:
    return max(low, min(val, high))
