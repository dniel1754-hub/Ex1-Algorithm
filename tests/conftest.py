import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LECTURER_CSV = ROOT / "data" / "lecturer_example.csv"


def random_isosceles(rng, size, trapezoid=False):
    """Points of a random valid triangle (a, b, c) or trapezoid (a1, b, a2, c) around a volume."""
    apex = rng.uniform(-0.2 * size, 1.2 * size, 3)
    base_mid = rng.uniform(-0.2 * size, 1.2 * size, 3)
    axis = base_mid - apex
    side = np.cross(axis, rng.normal(size=3))
    side /= np.linalg.norm(side)
    half_base = rng.uniform(0.2, 0.8) * np.linalg.norm(axis)
    b, c = base_mid - side * half_base, base_mid + side * half_base
    if not trapezoid:
        return [apex, b, c]
    half_top = rng.uniform(0, 1) * half_base
    return [apex - side * half_top, b, apex + side * half_top, c]


@pytest.fixture
def rng():
    return np.random.default_rng(1234)


@pytest.fixture
def coded_volume():
    """M[x, y, z] = x + 64*y + 4096*z, so every sample tells which voxel it came from."""
    x, y, z = np.meshgrid(np.arange(64), np.arange(64), np.arange(64), indexing="ij")
    return (x + 64 * y + 4096 * z).astype(np.uint32)


def decode(values):
    values = np.asarray(values, dtype=np.int64)
    return np.stack([values % 64, values // 64 % 64, values // 4096], axis=-1)
