"""Projection FPS on a 500^3 uint8 volume (TESTING.md section 4).

Times Projector.project() only: no file I/O, no video encoding.
Usage: python benchmarks/bench_projection.py [--runs 200] [--size 500]
"""
from __future__ import annotations

import argparse
import platform
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from projection import NumpyProjector, Projector, TrapezoidPlane, TrianglePlane, default_projector  # noqa: E402

REQUIRED_FPS, TARGET_FPS = 30, 100


def planes(s: float):
    """Large planes spanning most of an s^3 volume: axis-aligned and oblique."""
    return {
        "lecturer triangle": TrianglePlane((0.4 * s, 0.4 * s, 0), (0, 0.4 * s, 0.8 * s), (0.8 * s, 0.4 * s, 0.8 * s)),
        "lecturer rectangle": TrapezoidPlane((0.4 * s, 0, 0), (0.4 * s, 0, s), (0.4 * s, 0.8 * s, 0), (0.4 * s, 0.8 * s, s)),
        "oblique triangle": TrianglePlane((0, 0, 0), (s, 0, s), (0, s, s)),
        "oblique trapezoid": TrapezoidPlane((0.3 * s, 0, 0), (0, s, 0.2 * s), (0.7 * s, 0, 0), (s, s, 0.2 * s)),
        "diagonal slab": TrapezoidPlane((0, 0, 0), (0, s, s), (s, 0, 0), (s, s, s)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--size", type=int, default=500)
    args = parser.parse_args()

    volume = np.random.default_rng(0).integers(0, 256, (args.size,) * 3, dtype=np.uint8)
    print(f"{args.size}^3 uint8 volume, {args.runs} runs per plane | "
          f"Python {platform.python_version()}, NumPy {np.__version__}, {platform.processor() or platform.machine()}")

    projectors = [default_projector()]
    if not isinstance(projectors[0], NumpyProjector):
        projectors.append(NumpyProjector())          # for comparison
    results = {type(p).__name__: bench(p, volume, args.runs) for p in projectors}

    fps = results[type(projectors[0]).__name__]
    verdict = "PASS (target met)" if fps >= TARGET_FPS else "PASS (minimum only)" if fps >= REQUIRED_FPS else "FAIL"
    print(f"\n{type(projectors[0]).__name__} (used by Ex0.py): {fps:.0f} FPS -> {verdict}; "
          f"required {REQUIRED_FPS}, target {TARGET_FPS}")
    return 0 if fps >= REQUIRED_FPS else 1


def bench(projector: Projector, volume: np.ndarray, runs: int) -> float:
    """Print per-plane timings; return the overall mean FPS (worst planes weigh most)."""
    projector.warm_up(volume)
    print(f"\n{type(projector).__name__}")
    print(f"{'plane':<20}{'image':>11}{'mean FPS':>10}{'p95 ms':>9}")
    all_times = []
    for name, plane in planes(volume.shape[0]).items():
        for _ in range(5):
            projector.project(volume, plane)   # warm-up
        times = []
        for _ in range(runs):
            start = time.perf_counter()
            projector.project(volume, plane)
            times.append(time.perf_counter() - start)
        all_times += times
        h, w = projector.output_shape(plane)
        print(f"{name:<20}{f'{h}x{w}':>11}{1 / np.mean(times):>10.0f}{np.percentile(times, 95) * 1000:>9.2f}")
    return 1 / np.mean(all_times)


if __name__ == "__main__":
    sys.exit(main())
