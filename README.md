# Ex1: Plane Projection of a 3D Volume

Exercise 1 of *Introduction to Software Engineering (OOP/OOD)*, Ariel University.
Course repository: [benmoshe/Intro2SE](https://github.com/benmoshe/Intro2SE)

## Goal
Design and implement an under-specified algorithm in a robust, efficient and well-structured way. The emphasis is on software design and code quality, not only on the algorithm itself.

## Problem statement
We are given:
- a 3D raster volume **M** of size `sx × sy × sz` (`1 ≤ sx, sy, sz < 2^10`), whose entries are unsigned 8, 16 or 32-bit integers;
- a planar shape **p**, given by 3 points (an isosceles triangle) or 4 points (an isosceles trapezoid).

We compute a 2D image **E** by sampling M across p. Given a list of such shapes, we render one image per shape and write them, in order, as frames of an MP4 video.

## Scope
**In scope:**
- reading NRRD volumes and the plane CSV;
- validating the plane geometry;
- the projection algorithm;
- MP4 output;
- a command-line demo;
- tests and a performance benchmark.

**Out of scope:** a GUI, interpolation better than nearest neighbour, and physical (mm) coordinates. Coordinates are voxel indices.

## Documents
The documents follow the chain from the course's Design Docs lecture: **SRS** (what) → **SDD** (structure) → **EDD** (how one component is built) → **STP/STD** (how we prove it works), with a traceability matrix linking them.

| Document | Contents |
|---|---|
| [SRS.md](SRS.md) | Requirements (FR/NFR), use case UC-01 with its activity diagram, and the traceability matrix (Appendix A) |
| [SDD.md](SDD.md) | Architecture: context, components, classes, the sequence of a run, data, deployment (Mermaid diagrams) |
| [ALGORITHM.md](ALGORITHM.md) | Detailed design (EDD) of the projector, with measured performance |
| [TESTING.md](TESTING.md) | Test plan (STP) and test cases TC-01…TC-47 (STD) |
| [docs/adr/](docs/adr/) | Architecture Decision Records: why we chose what we chose |
| [AGENTS.md](AGENTS.md) | Instructions for AI coding agents: commands, rules, definition of done (also loaded by `CLAUDE.md`) |

## Input formats

### Volume: `.nrrd`
Any 3D NRRD volume with unsigned integer voxels.

### Planes: `.csv`
This is the format published with the assignment; see [data/lecturer_example.csv](data/lecturer_example.csv). There is one plane per row, and therefore one video frame per row:

```
Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
3,200,200,0,0,200,400,400,200,400,,,
4,200,0,0,200,0,500,200,400,0,200,400,500
```

- With 3 points, the row is `(a, b, c)`, where `a` is the apex.
- With 4 points, the row is `(a1, b, a2, c)`: the two legs `a1→b` and `a2→c`, one after the other. `a1–a2` is the short base.
- Blank lines and `#` comment lines are ignored.
- A row that fails validation (EPS = 0.001) produces a black frame and a warning. See [SRS FR-6](SRS.md#fr-6-invalid-planes).

## Dataset
We use the dataset shared by a classmate: [Google Drive folder](https://drive.google.com/drive/folders/1koJ83uaeMYdJt6AwvVlmMJk_wzczvmmG?usp=sharing). Each volume comes with a plane CSV (in `csv/`) and a reference image (in `images/`).

| Volume | Plane CSV | Notes |
|---|---|---|
| `MRHead_1.nrrd` | `head.csv` | MRI head from [3D Slicer](https://www.slicer.org/), the [course's recommended file](https://drive.google.com/file/d/1cqqOgSf8k4e14K5CBs-V_EvMmATX1K-J/view?usp=sharing). The CSV sweeps axial slices |
| `biscuit_cake.nrrd` | `biscuit_cake.csv` | Sweep of oblique trapezoids |
| `croissant.nrrd` | `croissant.csv` | Random oblique triangles |
| `onion.nrrd` | `onion.csv` | Sweep of oblique trapezoids |
| `swiss_roll.nrrd` | `swiss_roll.csv` | Sweep of oblique trapezoids |
| any volume | `lecturer_example.csv` | The course's sample CSV (also in [data/](data/lecturer_example.csv)): 3 valid planes and 1 non-isosceles triangle (row 3) |
| `dice.nrrd` (synthetic, not in the folder) | `edge_cases.csv` | Edge cases with expected results written in comments |

NRRD files are large and are not committed (see `.gitignore`). Download them from the folder into `data/`. The CSVs are committed in [data/](data/).

## Running
```bash
pip install -r requirements.txt
python Ex0.py data/MRHead_1.nrrd data/head.csv out.mp4      # the demo
python Ex0.py data/MRHead_1.nrrd data/head.csv out.mp4 --fps 30   # same frames, faster playback
python -m pytest                                            # the tests
python benchmarks/bench_projection.py                       # FPS on a 500³ volume
```

`Ex0.py` prints a warning for each invalid CSV row (and writes a black frame for it), then a summary with the projection FPS.

`--fps` sets the video's playback rate (default 10, up to 1000). It changes only how fast the MP4 plays, not how fast frames are projected: each CSV row is still one frame. Most screens show at most 60 frames per second, so higher rates skip frames on playback.

## Code layout
| Path | Contents |
|---|---|
| [Ex0.py](Ex0.py) | Command-line demo that wires the components together |
| [projection/geometry.py](projection/geometry.py) | `TrianglePlane`, `TrapezoidPlane` and their validation |
| [projection/plane_reader.py](projection/plane_reader.py) | `PlaneReader`: CSV → plane records (valid or with an error) |
| [projection/volume.py](projection/volume.py) | `Volume`: NRRD loading, intensity window |
| [projection/projector.py](projection/projector.py) | `NumbaProjector` (default) and `NumpyProjector` (fallback) |
| [projection/frame_composer.py](projection/frame_composer.py) | `FrameComposer`: 8-bit mapping and fixed-size canvas |
| [projection/video_writer.py](projection/video_writer.py) | `VideoWriter`: H.264 MP4 output |
| [tests/](tests/) | pytest suite |
| [benchmarks/](benchmarks/) | FPS benchmark |

## Progress
- [x] Repository, problem statement and scope (this README)
- [x] SRS
- [x] Detailed algorithm
- [x] Dataset of NRRD files
- [x] Testing strategy, including the demo
- [x] Implementation (commit frequently)
- [x] Demo `Ex0.py <file.nrrd> <file.csv> <file.mp4> [--fps N]`
- [x] Experiment: results on the class dataset and output `.mp4`

## Experiment results
**Projection speed** on a random `500³` uint8 volume, from `benchmarks/bench_projection.py`: **453–3823 FPS** with `NumbaProjector`, depending on the plane. The slowest is a large oblique 708 × 501 plane. The required minimum is 30 FPS and the target is 100. The per-plane table is in [ALGORITHM.md §5](ALGORITHM.md#5-implementation).

### Class dataset
Each volume from the [class dataset](https://drive.google.com/drive/folders/1koJ83uaeMYdJt6AwvVlmMJk_wzczvmmG?usp=sharing) was run with its own plane CSV, using `python Ex0.py data/<volume>.nrrd data/<csv>.csv experiment/<name>.mp4 --fps 30`. Each row has an output video in [experiment/](experiment/) and a strip of 6 sampled frames in [experiment/previews/](experiment/previews/).

| Volume | Size, type | CSV | Frames | Projection FPS | Video | Preview |
|---|---|---|---|---|---|---|
| MRHead_1 | 256×256×130, int16 | `head.csv` | 280 | 428 | [mp4](experiment/MRHead_1__head.mp4) | [png](experiment/previews/MRHead_1__head.png) |
| biscuit_cake | 256×256×130, uint16 | `biscuit_cake.csv` | 120 | 320 | [mp4](experiment/biscuit_cake.mp4) | [png](experiment/previews/biscuit_cake.png) |
| croissant | **500×500×500**, uint8 | `croissant.csv` | 100 | **299** | [mp4](experiment/croissant.mp4) | [png](experiment/previews/croissant.png) |
| croissant | 500×500×500, uint8 | `lecturer_example.csv` | 4 (1 black) | 490 | [mp4](experiment/croissant__lecturer_example.mp4) | [png](experiment/previews/croissant__lecturer_example.png) |
| onion | 256×256×130, uint8 | `onion.csv` | 120 | 1312 | [mp4](experiment/onion.mp4) | [png](experiment/previews/onion.png) |
| swiss_roll | 256×256×130, uint32 | `swiss_roll.csv` | 120 | 823 | [mp4](experiment/swiss_roll.mp4) | [png](experiment/previews/swiss_roll.png) |

**Observations**
- **Correctness.** The frames show the expected structures, matching the dataset's reference images (`images/` in the Drive folder): the head's sagittal sweep and the rotating planes, the croissant's layers, the swiss roll's spiral and its candles.
- **Every value type works.** The volumes cover int16, uint16, uint8 and uint32. Each video uses a single intensity window for the whole volume, so its brightness doesn't flicker from frame to frame.
- **Performance.** On real data, projection ran at 299–566 FPS on the 500³ croissant and 320–1772 FPS on the 256×256×130 volumes, over several runs. That is above the 100 FPS target every time. The average varies by up to about 2× between runs on the same machine, so the table shows the run that made the committed videos. Total run time is dominated by NRRD decompression and H.264 encoding, not by the projection.
- **Invalid rows.** The lecturer's row 3 is not isosceles. It was reported with a warning and written as a black frame, so frame *i* still matches row *i*.
- **Planes outside the volume.** The rotating planes in `head.csv` reach beyond the volume (z goes as low as −24). Those frames show only the part inside the volume and black elsewhere, with no errors.
- **Voxel versus physical space.** We work in voxel indices and ignore the NRRD voxel spacing. So volumes with non-cubic voxels look slightly squashed along the slice axis compared with the reference images, which are drawn in millimetres: MRHead's voxels are 1 × 1 × 1.3 mm and the swiss roll's are 1.1 × 1.1 × 1.43 mm. A possible extension is to resample by the `space directions` field.
- **Not run:** `edge_cases.csv`. It needs a synthetic `dice.nrrd`, which isn't in the shared folder.
