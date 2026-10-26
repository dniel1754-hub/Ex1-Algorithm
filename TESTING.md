# Testing Strategy

All automated tests use **pytest** and live under `tests/`. Most tests use small **synthetic volumes** built in memory. With these, the expected output can be computed exactly, and no NRRD files are needed. The strategy has four levels: unit, integration, end-to-end demo and performance.

## 1. Unit tests

### 1.1 Plane geometry and validation (`Plane`)
| Test | Expectation |
|---|---|
| Isosceles triangle, row 1 of the example CSV | Valid. `Dab = 447.21…`, `Dbc = 400` |
| Legs differ by `0.0005` | Valid (below EPS) |
| Legs differ by `0.002` | Invalid: not isosceles |
| Row 3 of the example CSV (legs 497.39 vs 476.86) | Invalid: not isosceles |
| Rectangle trapezoid, row 2 of the example CSV | Valid |
| Row 4 of the example CSV, read as `(a1, b, a2, c)` | Valid: legs 502.49 each, bases 300 ≤ 400 |
| Row 4 read in the wrong order `(a1, a2, b, c)` | Invalid (legs 300 vs 400). A regression test for the point order |
| Trapezoid with `dist(a1,a2) > dist(b,c)` | Invalid |
| Trapezoid whose 4th point is lifted off the plane | Invalid: not coplanar |
| Degenerate shapes (`a == b`, `b == c`, all points identical) | Invalid, with no division by zero |
| Leg step vectors `v1`, `v2` | Length is 1 within `1e-9` |

### 1.2 CSV parsing (`PlaneReader`)
- The example CSV gives 4 records: two triangles and two trapezoids, with the empty 4th point handled.
- The header is skipped, and blank lines and `#` comment lines are ignored (as in the class dataset's `edge_cases.csv`).
- All CSVs from the class dataset parse without errors.
- A wrong point count (for example `5`), a missing coordinate or a non-numeric value marks the row invalid with its row number. Parsing continues.
- Negative and floating-point coordinates are accepted.

### 1.3 Projection (`NumbaProjector` and `NumpyProjector`; every test runs on both)
Use synthetic volumes whose voxel value encodes its position:

| Test | Setup | Expectation |
|---|---|---|
| **Coordinate mapping** | `M[x,y,z] = x + 64y + 4096z` (uint32), so each value tells which voxel was sampled | Every sampled voxel lies within half a voxel diagonal of the plane |
| **Top edge and base** | Same volume | Row 0 samples the apex `a`. Row `H−1` samples points on `b–c`, with its first and last inside pixels at `b` and `c` |
| **Output size** | Any valid plane | `E.shape == (⌊Dleg⌋+1, ⌊Dbc⌋+1)` |
| **Shape mask** | Constant volume `M = 7` fully containing the triangle | Inside pixels are 7, outside pixels are 0. Each row's inside width is about `d12(y)` |
| **Out of bounds** | Triangle partly outside the volume (negative coordinates, like row 3) | Out-of-volume pixels are 0, with no `IndexError` |
| **Fully outside** | Plane entirely outside the volume | E is all 0 |
| **Axis order** | Volume with distinct `sx ≠ sy ≠ sz`, single bright voxel | The pixel lights up only when the plane passes through that `(x, y, z)` |
| **Value types** | Same test with uint8, uint16 and uint32 | Output dtype equals input dtype. Values above 255 are kept exactly |
| **Loop reference** | Random volume and plane | Both projectors are bit-identical to a slow, plain per-pixel loop |

### 1.4 Frame composition (`FrameComposer`)
- Intensity window: the volume minimum maps to 0, the maximum to 255, and the output is uint8. A constant volume is handled without dividing by zero.
- Canvas: E is placed top-aligned and horizontally centred. The canvas has the maximum size over all valid planes, with even dimensions.
- An invalid plane gives an all-black frame of canvas size.

## 2. Integration tests
- **NRRD loading.** Write a small synthetic volume with `pynrrd`, load it with `Volume`, and check that the shape, dtype and values match exactly, including axis order.
- **Sample file.** Load each class-dataset NRRD in `data/` (when present; skipped otherwise) and check that the shape matches the header `sizes`.
- **Pipeline.** Synthetic NRRD and a 3-row CSV produce an MP4 that reads back with `imageio` as exactly 3 frames of the expected size.

## 3. End-to-end demo validation
| Case | Command | Expectation |
|---|---|---|
| Lecturer example | `python Ex0.py data/MRHead_1.nrrd data/lecturer_example.csv out.mp4` | Exit code 0. `out.mp4` has **4 frames**: 3 images and 1 black frame, because row 3 is not isosceles, plus 1 warning on stderr |
| Class dataset | Each `<name>.nrrd` with its `<name>.csv` | One frame per row. Compare a sample of frames with the dataset's `images/<name>.png` |
| Wrong argument count | `python Ex0.py a.nrrd` | Usage message, non-zero exit code |
| Missing NRRD or CSV | Nonexistent path | Clear error message, non-zero exit code, no stack trace |
| Not an NRRD | A `.txt` file renamed to `.nrrd` | Clear error message, non-zero exit code |
| Playback | Open `out.mp4` | Plays in a standard player such as VLC or a browser |
| Visual check | Compare the frames for rows 1 and 2 with the same planes in 3D Slicer | Same anatomy and orientation |

## 4. Performance benchmark
- **Script:** `benchmarks/bench_projection.py`
- **Volume:** a random `500×500×500` uint8 volume.
- **Planes:** a set of large planes, including oblique ones (not axis-aligned), each spanning most of the volume.
- **Measurement:** time only `Projector.project()`, run at least 200 times after a warm-up, using `time.perf_counter`. Report mean FPS and p95 frame time.
- **Pass criteria:** mean ≥ **30 FPS** (required), with ≥ **100 FPS** as the target.
- **Results:** the measured numbers and the machine spec are recorded in the experiment section of the README.
