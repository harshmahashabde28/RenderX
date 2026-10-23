"""Typed 3D vector value object with standard mathematical operations."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt, isfinite


@dataclass(slots=True, frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    @classmethod
    def from_tuple(cls, point: tuple[float, float, float]) -> Vec3:
        return cls(float(point[0]), float(point[1]), float(point[2]))

    def to_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def is_finite(self) -> bool:
        return isfinite(self.x) and isfinite(self.y) and isfinite(self.z)

    def __add__(self, other: Vec3 | tuple[float, float, float]) -> Vec3:
        if isinstance(other, Vec3):
            return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
        return Vec3(self.x + other[0], self.y + other[1], self.z + other[2])

    def __sub__(self, other: Vec3 | tuple[float, float, float]) -> Vec3:
        if isinstance(other, Vec3):
            return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
        return Vec3(self.x - other[0], self.y - other[1], self.z - other[2])

    def __mul__(self, scalar: float) -> Vec3:
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> Vec3:
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide Vec3 by zero.")
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __neg__(self) -> Vec3:
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other: Vec3) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vec3) -> Vec3:
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y + self.z * self.z

    def length(self) -> float:
        return sqrt(self.length_squared())

    def distance_to(self, other: Vec3) -> float:
        return (self - other).length()

    def normalized(self) -> Vec3:
        l = self.length()
        if l == 0:
            return Vec3(0.0, 0.0, 0.0)
        return self / l
