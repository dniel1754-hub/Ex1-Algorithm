# Algorithm Definition: 3D to 2D Plane Projection

## 1. Approach: backward mapping
To meet the performance requirement (≥ 30 FPS on a `500³` volume), we never iterate over the voxels of the volume. Iterating over all of them to find the ones that intersect the plane would cost `O(sx·sy·sz)` per frame.

Instead we use **backward mapping**: we iterate over the pixels of the output image E, compute the 3D point on the plane that each pixel represents, and sample the volume M there. The cost per frame is `O(H·W)`, the size of the output image, and does not depend on the size of the volume.

## 2. Geometric setup

### Case A: 3 points, isosceles triangle `(a, b, c)`
`a` is the apex and `b–c` is the base. The scan starts with both boundary points at the apex: `a1 = a2 = a`. The legs are `a→b` and `a→c`.

### Case B: 4 points, isosceles trapezoid `(a1, b, a2, c)`
The CSV lists the two legs one after the other: `a1→b`, then `a2→c` (SRS FR-2).
`a1–a2` is the top (short) base and `b–c` is the bottom (long) base. The scan starts at the two top vertices. The legs are `a1→b` and `a2→c`.

Both cases are handled by one algorithm: a triangle is a trapezoid whose top base has length 0. Each plane is validated first (SRS FR-3, `EPS = 0.001`).

### Common initialization
- `D1 = dist(a1, b)` and `D2 = dist(a2, c)` are the leg lengths, with `|D1 − D2| < EPS`. Let `Dleg = D1`.
- `Dbc = dist(b, c)` is the bottom base length.
- The unit step vectors along the legs are:
  - `v1 = (b − a1) / D1`
  - `v2 = (c − a2) / D2`
- The output size is `H = ⌊Dleg⌋ + 1` rows and `W = ⌊Dbc⌋ + 1` columns, so both the top and the bottom edge are included.

## 3. Scanning

### Rows (y axis)
For `y = 0 … H−1`, the boundary points are:

```
a1(y) = a1 + y·v1
a2(y) = a2 + y·v2
```

Row 0 lies on the top edge (the apex for a triangle) and row `H−1` lies on the bottom base.

> **Deviation from the course pseudocode.** The pseudocode advances `a1` and `a2` *before* sampling, so it never samples the apex row. Starting at `y·v` instead of `(y+1)·v` includes both the top edge and the bottom base.

### Columns (x axis)
For row `y`:
- `d12(y) = dist(a1(y), a2(y))` is the width of the shape on that row.
- `dp(y) = (a2(y) − a1(y)) / d12(y)` is the unit step along the row. When `d12 < EPS` (the apex row of a triangle), `dp = 0` and the row has a single sample.

The row is **centred** in E: its left end is at column `Dbc/2 − d12(y)/2`. For output column `x`, the position along the row is:

```
x1 = x − (Dbc/2 − d12(y)/2)
```

The pixel is **inside the shape** when `−½ ≤ x1 ≤ d12(y) + ½`, meaning its pixel cell touches the row's span. Its 3D sample point is taken at the nearest point on the span:

```
p(y, x) = a1(y) + clamp(x1, 0, d12(y)) · dp(y)
```

> **Why the half-pixel margin.** Without it, a row narrower than one pixel (for example the apex row of a triangle) could fall between two integer columns and disappear. With the margin, every row has at least one pixel. Clamping keeps every sample on the shape itself.

> **Why we invert the column formula.** The course pseudocode walks `x1 = 0, 1, …` and writes to the column `x = Dbc/2 − d12/2 + x1`, which is usually not a whole number. Rounding it can leave gaps or write the same pixel twice. Computing `x1` from every integer column `x` is pure backward mapping: every pixel of E is computed exactly once.

## 4. Sampling and edge cases
- **Nearest neighbour.** `p` is rounded to the nearest integer index `(i, j, k)`, and `v = M[i][j][k]`. This is the fastest method and does not create values that aren't in the data.
- **Outside the volume.** If `(i, j, k)` is outside `[0, sx) × [0, sy) × [0, sz)`, then `v = 0`. Points with negative coordinates are allowed and simply fall outside.
- **Outside the shape.** Pixels with `x1 < −½` or `x1 > d12(y) + ½` are `0`.
- **Storage.** E is stored row-major as `E[y, x]`, the usual image layout. This is the same pixel the pseudocode calls `E[x][y]`.
- **Value type.** E has the same dtype as M (uint8, uint16 or uint32). Conversion to 8 bits happens later, when the frame is composed (SRS FR-5).

## 5. Implementation
The per-row values `a1(y)`, `dp(y)`, `d12(y)` and the start column are computed once per frame as small `(H, 3)` arrays (`Projector._rows`). The per-pixel step then has two interchangeable implementations ([projection/projector.py](projection/projector.py)):

| Class | How | Notes |
|---|---|---|
| `NumbaProjector` (default) | A compiled loop over the rows in parallel (`numba.prange`). Each pixel is computed once, as in §3–4 | Used by `Ex0.py` |
| `NumpyProjector` (fallback) | The same formulas as whole-array `(H, W)` operations. Bounds are checked with a single unsigned compare, then one `np.take` on a flat view of the volume | Used when Numba is not installed |

The two do the same floating-point operations in the same order, and the tests check that their output is **bit-identical** to a plain per-pixel reference loop.

**Measured on a random `500³` uint8 volume** (`benchmarks/bench_projection.py`, Intel laptop CPU, 12 threads):

| Plane | Image | Numba FPS | NumPy FPS |
|---|---|---|---|
| Lecturer triangle (axis-aligned) | 448 × 401 | 3823 | 103 |
| Lecturer rectangle (axis-aligned) | 501 × 401 | 2405 | 56 |
| Oblique triangle | 708 × 708 | 836 | 22 |
| Oblique trapezoid | 532 × 501 | 654 | 40 |
| Diagonal slab | 708 × 501 | 453 | 27 |

**Why NumPy alone isn't enough.** It meets the targets on axis-aligned planes but drops below 30 FPS on large oblique ones. The volume lookups take only about 5 ms of a 30 ms frame; the rest is the dozen full-array passes needed to compute coordinates. A compiled loop does all of that in one pass per pixel.

## 6. Return value
The algorithm returns E, an `H × W` image with the dtype of M. It is one projected frame of the volume on the given plane.
