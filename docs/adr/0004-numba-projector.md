# ADR-0004: Numba-compiled projector, with a NumPy fallback

- **Status:** Accepted
- **Date:** 2026-10-26
- **Requirements:** SRS NFR-1 (≥ 30 FPS required, 100 FPS target on `500³`), NFR-4

## Context
The design first planned a fully vectorized NumPy projector. On a random `500³` uint8 volume it measured:

| Plane | Image | NumPy FPS |
|---|---|---|
| Lecturer triangle (axis-aligned) | 448 × 401 | 103 |
| Oblique triangle | 708 × 708 | **22** |
| Diagonal slab | 708 × 501 | **27** |

That is below the 30 FPS minimum on large oblique planes. Profiling showed that only about 5 ms of a roughly 30 ms frame went to the volume lookups. The rest was a dozen full-array passes, each allocating, to compute and bounds-check the coordinates.

## Decision
- **The default `NumbaProjector`** is the same algorithm written as a per-pixel loop, compiled with `numba.njit(parallel=True, cache=True)`, with rows split across cores. It does one pass per pixel and allocates nothing besides E.
- **`NumpyProjector` stays as a fallback** when Numba is not installed. `default_projector()` chooses between them.
- Both implementations do the same floating-point operations in the same order, and are tested to be bit-identical (TC-30).

## Consequences
- **Performance:** 453–3823 FPS on the benchmark planes, and 299–566 FPS on the real 500³ croissant volume. That is far above the target, even on the worst plane.
- **New dependency:** `numba`. The first run compiles in about 1 s, and the result is cached in `__pycache__`. `Ex0.py` calls `warm_up()` before timing, so the reported FPS excludes compilation.
- **Two implementations to maintain.** This is mitigated by shared row geometry (`Projector._rows`) and by running every projection test on both.

## Alternatives considered
- **Optimize NumPy further** (float32 temporaries, preallocated buffers): this gains less than 2×, and oblique planes would still be borderline.
- **A C extension or Cython:** fast, but it needs a compiler toolchain on every machine. Numba installs from pip.
- **GPU (CuPy or CUDA):** not needed at these speeds, and not available on every machine. The course lists CUDA as a separate project idea (#5).
