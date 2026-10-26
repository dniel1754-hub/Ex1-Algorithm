"""Backward-mapping plane projection (ALGORITHM.md).

Two interchangeable implementations share the row geometry:
- NumbaProjector: a compiled per-pixel loop over rows in parallel (default, fastest).
- NumpyProjector: the same algorithm vectorized with NumPy (fallback without Numba).
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod

import numpy as np

from .geometry import Plane

# A pixel is inside a row when its position along the row is within half a pixel
# of the row's span; its sample point is then clamped onto the span.
HALF_PIXEL = 0.5
_TINY = 1e-12


class Projector(ABC):
    """Computes the image E of a plane through a 3D array indexed as M[x, y, z]."""

    @staticmethod
    def output_shape(plane: Plane) -> tuple[int, int]:
        """(H, W) = (floor(leg) + 1, floor(base) + 1): top edge and base both included."""
        return math.floor(plane.leg_length) + 1, math.floor(plane.base_length) + 1

    @abstractmethod
    def project(self, volume: np.ndarray, plane: Plane) -> np.ndarray:
        """Return E with shape output_shape(plane) and the volume's dtype."""

    def warm_up(self, volume: np.ndarray) -> None:
        """Do any one-time setup for this volume's type, so timing excludes it."""

    @staticmethod
    def _rows(plane: Plane, h: int):
        """Per row y: left boundary a1(y), unit step dp(y) towards a2(y), width d12(y), start column."""
        y = np.arange(h, dtype=np.float64)[:, None]
        v1 = (plane.b - plane.a1) / np.linalg.norm(plane.b - plane.a1)
        v2 = (plane.c - plane.a2) / np.linalg.norm(plane.c - plane.a2)
        a1_rows = plane.a1 + y * v1                      # (H, 3)
        span = (plane.a2 + y * v2) - a1_rows             # (H, 3) vector a1(y) -> a2(y)
        d12 = np.linalg.norm(span, axis=1)               # (H,)
        dp = span / np.maximum(d12, _TINY)[:, None]      # (H, 3)
        left = plane.base_length / 2 - d12 / 2           # centred row start column
        return a1_rows, dp, d12, left


class NumpyProjector(Projector):
    """Vectorized: every pixel of E is computed with whole-array operations."""

    def project(self, volume: np.ndarray, plane: Plane) -> np.ndarray:
        h, w = self.output_shape(plane)
        a1_rows, dp, d12, left = self._rows(plane, h)
        x1 = np.arange(w, dtype=np.float64)[None, :] - left[:, None]   # (H, W) position along the row
        row_end = d12[:, None]
        valid = (x1 >= -HALF_PIXEL) & (x1 <= row_end + HALF_PIXEL)
        np.clip(x1, 0, row_end, out=x1)

        flat, elem_strides = _flat_view(volume)
        offset = np.zeros((h, w), dtype=np.int64)
        coord = np.empty((h, w), dtype=np.float64)
        for axis in range(3):
            np.multiply(x1, dp[:, axis, None], out=coord)
            coord += a1_rows[:, axis, None]
            index = np.rint(coord, out=coord).astype(np.int32)
            # One unsigned compare checks 0 <= index < size (negatives wrap to huge values).
            valid &= index.view(np.uint32) < volume.shape[axis]
            offset += index * np.int64(elem_strides[axis])

        offset[~valid] = 0
        image = flat.take(offset)
        image[~valid] = 0
        return image


class NumbaProjector(Projector):
    """Compiled loop: rows run in parallel, each pixel is computed once."""

    def __init__(self):
        from ._kernel import project_rows  # imports numba; raises ImportError without it
        self._kernel = project_rows

    def project(self, volume: np.ndarray, plane: Plane) -> np.ndarray:
        h, w = self.output_shape(plane)
        a1_rows, dp, d12, left = self._rows(plane, h)
        image = np.empty((h, w), dtype=volume.dtype)
        self._kernel(volume, a1_rows, dp, d12, left, image, HALF_PIXEL)
        return image

    def warm_up(self, volume: np.ndarray) -> None:
        from .geometry import TrianglePlane
        self.project(volume, TrianglePlane((0, 0, 0), (-1, 2, 0), (1, 2, 0)))  # compiles for this dtype/layout


def default_projector() -> Projector:
    try:
        return NumbaProjector()
    except ImportError:
        return NumpyProjector()


def _flat_view(volume: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int]]:
    """A 1D view of the volume plus the element stride of each axis, for np.take."""
    if not (volume.flags.c_contiguous or volume.flags.f_contiguous):
        volume = np.ascontiguousarray(volume)
    strides = tuple(s // volume.itemsize for s in volume.strides)
    return volume.reshape(-1, order="A"), strides
