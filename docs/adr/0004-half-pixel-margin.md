# ADR-0004: Half-pixel margin, with samples clamped onto the row

- **Status:** Accepted
- **Date:** 2026-10-26
- **Requirements:** SRS FR-4. Details in ALGORITHM.md §3

## Context
Each image row `y` holds the segment from `a1(y)` to `a2(y)`, of length `d12(y)`, centred in a row of width `⌊Dbc⌋ + 1`. Integer output column `x` maps to position `x1 = x − (Dbc/2 − d12/2)` along the segment.

If a pixel counts as inside only when `0 ≤ x1 ≤ d12`, a row narrower than one pixel, such as a triangle's apex row, can fall between two integer columns and vanish. The shape then gets ragged, one-pixel-short edges.

## Decision
- A pixel is inside when `−½ ≤ x1 ≤ d12 + ½`, meaning its pixel cell touches the segment.
- Its sample point is taken at `clamp(x1, 0, d12)`, so every sample lies on the shape itself.

## Consequences
- Every row has at least one pixel. The apex is always drawn, and edges are symmetric.
- Samples never leave the plane shape, so values from outside the triangle or trapezoid cannot leak in (TC-23).
- Edge pixels are about half a pixel wider than the exact outline, which is invisible at this resolution.

## Alternatives considered
- **Exact `0 ≤ x1 ≤ d12`:** rejected, because the apex row can disappear.
- **The course pseudocode's forward loop**, which walks `x1 = 0, 1, …` and rounds the column: rejected. Rounding can leave gaps or hit a pixel twice. Our backward mapping computes each pixel exactly once.
