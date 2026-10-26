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
| Document | Contents |
|---|---|
| [SRS.md](SRS.md) | Requirements, input formats, error handling, component design |
| [ALGORITHM.md](ALGORITHM.md) | Detailed projection algorithm and its vectorized implementation |
| [TESTING.md](TESTING.md) | Unit, integration, demo and performance testing |

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

NRRD files are large and are not committed (see `.gitignore`). Download the folder's contents into `data/`.

## Running the demo
```bash
pip install numpy pynrrd imageio imageio-ffmpeg
python Ex0.py data/MRHead_1.nrrd data/head.csv out.mp4
```

## Progress
- [x] Repository, problem statement and scope (this README)
- [x] SRS
- [x] Detailed algorithm
- [x] Dataset of NRRD files
- [x] Testing strategy, including the demo
- [ ] Implementation (commit frequently)
- [ ] Demo `Ex0.py <file.nrrd> <file.csv> <file.mp4>`
- [ ] Experiment: results, FPS benchmark and output `.mp4`

## Experiment results
*To be added after implementation: FPS on a `500³` volume, the machine spec, and the output video.*
