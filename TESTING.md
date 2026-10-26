# Testing: Test Plan (STP) and Test Description (STD)

Sections 1–4 are the **test plan**: what we test, how, and when we are done. Section 5 is the **test description**: every test case with its ID, the requirement it verifies and its expected result. [SRS Appendix A](SRS.md#appendix-a-traceability-matrix) maps each requirement to these IDs.

## 1. Scope
- **Under test:** the `projection` package, `Ex0.py` and `benchmarks/bench_projection.py`.
- **Not under test:** pynrrd, NumPy, Numba and ffmpeg themselves. Their output is checked only through ours, for example by reading the MP4 back.

## 2. Levels and approach
| Level | What | How |
|---|---|---|
| Unit | Geometry, CSV parsing, projection, frame composition | pytest with small **synthetic volumes**, where the right answer is known exactly. For example, in `M[x,y,z] = x + 64y + 4096z` each value tells which voxel was sampled |
| Integration | NRRD round trip, the full pipeline to MP4 | pytest. Writes temporary NRRD and CSV files, runs `Ex0.main` and reads the MP4 back with imageio |
| System | The class dataset, edge cases, error paths | pytest (`test_dataset.py`, `test_volume_and_cli.py`), plus a manual visual check against the dataset's reference images |
| Performance | Projection FPS on `500³` | `benchmarks/bench_projection.py` |

- **Both projectors.** Every projection test runs on both `NumbaProjector` and `NumpyProjector`, and both must be **bit-identical** to a plain per-pixel reference loop (TC-30).
- **Tools:** pytest 8+, Python 3.10+. The versions used are listed in `requirements.txt`.

## 3. Environment and test data
| Data | Where | Used by |
|---|---|---|
| Synthetic volumes | Built in memory or in pytest's `tmp_path` | Most tests |
| `data/lecturer_example.csv` | Committed | TC-15, TC-20, TC-45 |
| Class dataset CSVs (`data/*.csv`) | Committed | TC-20, TC-43 |
| Class dataset NRRDs (`data/*.nrrd`) | Downloaded from the class Drive folder; not committed | TC-39 (skipped when absent), TC-45 |
| `dice.nrrd` from `edge_cases.csv` | Rebuilt in the test from its description (without the pips) | TC-43 |

## 4. Entry and exit criteria
- **Entry:** the code imports, and `pip install -r requirements.txt` succeeds.
- **Exit (done):**
  - `python -m pytest` passes, with no failures and skips only for NRRDs that weren't downloaded.
  - `bench_projection.py` exits 0, meaning at least 30 FPS (NFR-1).
  - Manual cases TC-45 and TC-46 have been checked.
- **Definition of done for any change:** its tests and docs are updated in the same pull request, including the traceability matrix if a requirement changes.

## 5. Test description (STD)
Unless marked otherwise, each case is an automated pytest function in `tests/`. "Both" means the case runs on both projectors.

### 5.1 Plane geometry and validation (`test_geometry.py`)
| ID | Test | Verifies | Input | Expected |
|---|---|---|---|---|
| TC-01 | `test_lecturer_triangle_is_valid` | FR-3 | Lecturer row 1 | Valid triangle, legs 447.2136, base 400 |
| TC-02 | `test_lecturer_rectangle_is_valid` | FR-3 | Lecturer row 2 | Valid, legs 500, bases 400 and 400 |
| TC-03 | `test_lecturer_non_isosceles_triangle_is_invalid` | FR-3 | Lecturer row 3 (legs 497.39 vs 476.86) | `InvalidPlaneError`: legs differ |
| TC-04 | `test_lecturer_row_4_is_valid_in_leg_order` | FR-2, FR-3 | Lecturer row 4 as `a1, b, a2, c` | Valid, legs 502.49, bases 300 and 400 |
| TC-05 | `test_lecturer_row_4_in_wrong_order_is_invalid` | FR-2 | Row 4 as `a1, a2, b, c` | Invalid: guards the point order (ADR-0001) |
| TC-06 | `test_leg_difference_against_eps` | FR-3 | Legs differ by 0.0005, and by 0.002 | Valid, and invalid |
| TC-07 | `test_trapezoid_with_longer_top_is_invalid` | FR-3 | `dist(a1,a2) > dist(b,c)` | Invalid |
| TC-08 | `test_trapezoid_with_crossed_legs_is_invalid` | FR-3 | Row 2 with `a1` and `a2` swapped (a bow tie) | Invalid: legs cross |
| TC-09 | `test_oversized_plane_is_invalid` | FR-3, NFR-2 | Base of 4000 voxels | Invalid: too large |
| TC-10 | `test_trapezoid_off_plane_is_invalid` | FR-3 | Equal legs, `a2` lifted 3 off the plane | Invalid: not coplanar |
| TC-11 | `test_degenerate_shapes_are_invalid` | FR-3, NFR-2 | Identical points, `b == c`, apex on the base line, 2 points | Invalid, with no division by zero |
| TC-12 | `test_non_finite_coordinates_are_invalid` | FR-3, NFR-2 | A NaN coordinate | Invalid |
| TC-13 | `test_random_isosceles_shapes_are_valid` | FR-3 | 100 random isosceles triangles and trapezoids | All valid |
| TC-14 | `test_triangle_is_trapezoid_with_zero_top` | FR-4 | Any triangle | `a1 == a2` and top length 0 (one code path) |

### 5.2 CSV parsing (`test_plane_reader.py`, `test_dataset.py`)
| ID | Test | Verifies | Input | Expected |
|---|---|---|---|---|
| TC-15 | `test_lecturer_example` | FR-2, FR-6 | `lecturer_example.csv` | 4 records, frames 1–4. Row 3 is invalid with "legs differ" |
| TC-16 | `test_header_blank_and_comment_lines_are_skipped` | FR-2 | Header, blank lines and `#` lines mixed with rows | Only data rows become records, with correct frame and line numbers |
| TC-17 | `test_file_without_header` | FR-2 | First line is data | Parsed as frame 1 |
| TC-18 | `test_negative_and_float_coordinates` | FR-2 | Negative and decimal values | Valid, values kept exactly |
| TC-19 | `test_malformed_rows_are_invalid_and_parsing_continues` | FR-2, FR-6, NFR-2 | 7 malformed rows: bad count, missing value, text, extra values | Each is invalid with a reason, and the next row still parses |
| TC-20 | `test_dataset_csv_parses` | FR-2, FR-3 | All 7 class CSVs | Invalid frames are exactly as expected: none for the volume CSVs, `[3]` for the lecturer CSV, `[7, 9–16]` for `edge_cases.csv` |

### 5.3 Projection (`test_projector.py`; every case runs on both projectors)
| ID | Test | Verifies | Input | Expected |
|---|---|---|---|---|
| TC-21 | `test_output_shape` | FR-4 | Triangle with legs 51 and base 48 | E is 52 × 49 |
| TC-22 | `test_apex_and_base_corners` | FR-4 | Coded volume | Row 0 samples the apex. The last row's ends sample `b` and `c` |
| TC-23 | `test_every_sample_lies_on_the_plane` | FR-4 | 40 random planes, coded volume | Every sampled voxel is within √3/2 of the plane |
| TC-24 | `test_shape_mask_on_constant_volume` | FR-4 | Constant volume of 7 | One pixel at the apex, widening rows, each a single centred run |
| TC-25 | `test_out_of_bounds_samples_are_zero` | FR-4, NFR-2 | Triangle partly outside the volume | Outside pixels are 0, with no `IndexError` |
| TC-26 | `test_plane_fully_outside_is_black` | FR-4 | Plane far outside | All zeros |
| TC-27 | `test_axis_order` | FR-1, FR-4 | One bright voxel in a 40×30×20 volume | Seen only by the plane through that `(x, y, z)` |
| TC-28 | `test_dtype_is_kept` | FR-1, FR-4 | uint8, uint16, uint32 at their maximum value | Output has the same dtype and value |
| TC-29 | `test_fortran_and_non_contiguous_volumes` | FR-4, NFR-4 | Fortran-order and strided views | Same image as C order |
| TC-30 | `test_matches_reference_loop` | FR-4, NFR-1, NFR-4 | 20 random planes, random volume | Bit-identical to the plain per-pixel loop |
| TC-31 | `test_lecturer_trapezoid_is_a_full_rectangle` | FR-4 | Lecturer row 2 in a 500³ volume | 501 × 401. All rows filled except the last, at z = 500, which is outside |

### 5.4 Frame composition (`test_frame_composer.py`)
| ID | Test | Verifies | Input | Expected |
|---|---|---|---|---|
| TC-32 | `test_window_maps_min_to_0_and_max_to_255` | FR-5 | Window 100–1100 | 100 → 0, 600 → 127, ≥1100 → 255, as uint8 |
| TC-33 | `test_constant_volume_does_not_divide_by_zero` | FR-5, NFR-2 | Window 7–7 | All zeros, no error |
| TC-34 | `test_canvas_is_max_size_rounded_up_to_even` | FR-5 | Shapes 52×49, 501×401, 10×600 | Canvas 502 × 600 |
| TC-35 | `test_image_is_top_aligned_and_centred` | FR-5 | 3×4 image on a 6×8 canvas | Placed at rows 0–2, columns 2–5 |
| TC-36 | `test_blank_frame_and_too_large_image` | FR-5, FR-6 | — | The blank frame is black at canvas size. An oversized image raises `ValueError` |

### 5.5 Volume, CLI and system (`test_volume_and_cli.py`, `test_dataset.py`)
| ID | Test | Verifies | Input | Expected |
|---|---|---|---|---|
| TC-37 | `test_nrrd_round_trip_keeps_axis_order_and_type` | FR-1 | Coded uint32 volume written with pynrrd | Shape, dtype, values and `[x, y, z]` order are kept. The window is correct |
| TC-38 | `test_load_errors` | FR-1, NFR-2 | Missing file, text file, 2D array | `VolumeLoadError` with a clear message |
| TC-39 | `test_dataset_volume_loads` | FR-1 | Each class NRRD, if downloaded | Shape equals the header `sizes`. Skipped when the file is absent |
| TC-40 | `test_demo_writes_one_frame_per_row` | FR-5, FR-6, FR-7, UC-01 | 3-row CSV with one invalid row | Exit code 0, warning for frame 2, 3 frames of 52×50, frame 2 black, other frames match the expected images |
| TC-41 | `test_demo_errors` | FR-7, NFR-2, UC-01 | Wrong argument count, missing NRRD or CSV, non-NRRD, missing output folder | Exit codes 2 / 1 / 1 / 1 / 1 with the matching message |
| TC-42 | `test_demo_fails_when_no_plane_is_valid` | FR-6, UC-01 | CSV with only an invalid row | Exit code 1, "no valid planes" |
| TC-43 | `test_edge_cases_on_dice` | FR-3, FR-4, FR-6, UC-01 | The classmate's `edge_cases.csv` on the rebuilt die volume | 16 frames. Warnings for frames 7 and 9–16. Black frames 6, 7 and 9–16 |

### 5.6 Performance and manual cases
| ID | Test | Verifies | Procedure | Expected | Last result |
|---|---|---|---|---|---|
| TC-44 | `benchmarks/bench_projection.py` | NFR-1 | Run the script | Default projector ≥ 30 FPS (target 100), exit code 0 | 453–3823 FPS (Numba), passed |
| TC-45 | Class dataset experiment (manual) | FR-4, FR-5, UC-01 | Run `Ex0.py` on each class volume with its CSV, then compare the frames in `experiment/previews/` with the dataset's `images/*.png` | Same structures. Views follow the voxel axes, so they may be rotated relative to the anatomical views, and volumes with non-cubic voxels look squashed (ADR-0003) | Passed for all 5 volumes, 2026-10-26 |
| TC-46 | Playback (manual) | FR-5 | Open the `experiment/*.mp4` files in a browser or VLC | Plays, with duration = frames ÷ 10 FPS | Passed in Chromium for `swiss_roll.mp4` (12 s, 256×256). The rest were decoded with ffmpeg only |
