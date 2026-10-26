"""Plane shapes (isosceles triangle / trapezoid) and their validation (SRS FR-3)."""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

EPS = 1e-3


class InvalidPlaneError(ValueError):
    """Raised when points do not form a valid plane shape."""


def _point(p) -> np.ndarray:
    arr = np.asarray(p, dtype=np.float64)
    if arr.shape != (3,) or not np.all(np.isfinite(arr)):
        raise InvalidPlaneError(f"point must be 3 finite numbers, got {p!r}")
    return arr


def _dist(p: np.ndarray, q: np.ndarray) -> float:
    return float(np.linalg.norm(q - p))


class Plane(ABC):
    """A planar shape scanned from its top edge a1-a2 down to its base b-c.

    The legs are a1->b and a2->c. For a triangle a1 == a2 (the apex).
    """

    def __init__(self, a1, b, a2, c):
        self.a1, self.b, self.a2, self.c = (_point(p) for p in (a1, b, a2, c))
        self.validate()

    @property
    def leg_length(self) -> float:
        return _dist(self.a1, self.b)

    @property
    def base_length(self) -> float:
        return _dist(self.b, self.c)

    @property
    def top_length(self) -> float:
        return _dist(self.a1, self.a2)

    @abstractmethod
    def validate(self) -> None:
        """Raise InvalidPlaneError if the shape breaks the spec's conditions."""

    def _check_legs(self, first: float, second: float) -> None:
        if min(first, second) < EPS:
            raise InvalidPlaneError("a leg has zero length")
        if abs(first - second) >= EPS:
            raise InvalidPlaneError(f"legs differ: {first:.3f} vs {second:.3f}")

    def _base_normal(self) -> np.ndarray:
        """Unit normal of the plane through a1, b, c."""
        n = np.cross(self.c - self.b, self.b - self.a1)
        length = np.linalg.norm(n)
        if self.base_length < EPS or length < EPS:
            raise InvalidPlaneError("points are collinear or the base has zero length")
        return n / length

    def __repr__(self) -> str:
        pts = ", ".join(np.array2string(p, precision=2) for p in (self.a1, self.b, self.a2, self.c))
        return f"{type(self).__name__}({pts})"


class TrianglePlane(Plane):
    """Isosceles triangle with apex a and base b-c."""

    def __init__(self, a, b, c):
        super().__init__(a, b, a, c)

    def validate(self) -> None:
        self._check_legs(_dist(self.a1, self.b), _dist(self.a1, self.c))
        self._base_normal()


class TrapezoidPlane(Plane):
    """Isosceles trapezoid with legs a1->b and a2->c, short base a1-a2."""

    def validate(self) -> None:
        self._check_legs(_dist(self.a1, self.b), _dist(self.a2, self.c))
        if self.top_length > self.base_length + EPS:
            raise InvalidPlaneError(
                f"top base {self.top_length:.3f} is longer than bottom base {self.base_length:.3f}")
        off_plane = abs(float(np.dot(self.a2 - self.a1, self._base_normal())))
        if off_plane >= EPS:
            raise InvalidPlaneError(f"points are not coplanar (off by {off_plane:.3f})")


def plane_from_points(points) -> Plane:
    """Build a plane from 3 points (a, b, c) or 4 points in leg order (a1, b, a2, c)."""
    points = list(points)
    if len(points) == 3:
        return TrianglePlane(*points)
    if len(points) == 4:
        return TrapezoidPlane(*points)
    raise InvalidPlaneError(f"expected 3 or 4 points, got {len(points)}")
