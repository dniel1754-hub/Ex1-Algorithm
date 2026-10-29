"""The 3D volume M (SRS FR-1)."""
from __future__ import annotations

from functools import cached_property
from pathlib import Path

import numpy as np

MAX_AXIS = 2 ** 10 - 1


class VolumeLoadError(Exception):
    """Raised when a file cannot be read as a supported 3D volume."""


class Volume:
    """A 3D array indexed as data[x, y, z] in voxel coordinates."""

    def __init__(self, data: np.ndarray):
        data = np.asarray(data)
        if data.ndim != 3:
            raise VolumeLoadError(f"expected a 3D volume, got {data.ndim} dimensions")
        if not all(1 <= s <= MAX_AXIS for s in data.shape):
            raise VolumeLoadError(f"each axis must be 1..{MAX_AXIS}, got {data.shape}")
        if not (np.issubdtype(data.dtype, np.integer) or np.issubdtype(data.dtype, np.floating)):
            raise VolumeLoadError(f"unsupported voxel type {data.dtype}")
        self.data = data

    @classmethod
    def load(cls, path: str | Path) -> "Volume":
        import nrrd  # local import: tests that use synthetic arrays need no pynrrd

        try:
            data, _header = nrrd.read(str(path))  # default index order 'F' -> data[x, y, z]
        except FileNotFoundError:
            raise VolumeLoadError(f"file not found: {path}") from None
        except Exception as e:
            raise VolumeLoadError(f"cannot read NRRD file {path}: {e}") from None
        return cls(data)

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.data.shape

    @property
    def dtype(self) -> np.dtype:
        return self.data.dtype

    @cached_property
    def window(self) -> tuple[float, float]:
        """(min, max) of the voxel values, used for one shared intensity mapping."""
        return float(self.data.min()), float(self.data.max())
