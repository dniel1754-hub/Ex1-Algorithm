# ADR-0003: Coordinates are voxel indices; NRRD spacing is ignored

- **Status:** Accepted
- **Date:** 2026-10-26
- **Requirements:** SRS FR-1, FR-4

## Context
The assignment defines M as a matrix indexed `M[x][y][z]` with `0 ≤ x < sx`, and so on. It defines distances between plane points as plain Euclidean distances, and E as `Dab × Dbc` pixels. NRRD files can also carry physical geometry: `space directions` (voxel size and orientation) and `space origin`. In the class dataset, MRHead has 1 × 1 × 1.3 mm voxels, and the swiss roll 1.1 × 1.1 × 1.43 mm.

## Decision
CSV coordinates are **voxel indices** into the array exactly as pynrrd loads it (Fortran order, so `data[x, y, z]`). The voxel spacing and origin are ignored. One step along a plane is one voxel unit.

## Consequences
- This matches the assignment's definition of M, its distance-based image size, and the lecturer's sample CSV, whose coordinates fit a 500³ index space.
- It needs no resampling, so it is fast and simple.
- Volumes with non-cubic voxels look slightly squashed along the slice axis compared with millimetre views, such as the class dataset's reference images or 3D Slicer.
- Views follow the voxel axes, so they can be rotated relative to the anatomical axial, coronal and sagittal views.

## Alternatives considered
- **Physical (mm) coordinates:** CSV points in scanner space, mapped to indices through the inverse of `space directions`. Rejected for now, because it contradicts the assignment's index-based definition and would make the lecturer's CSV meaningless. It is a possible extension behind a command-line flag.
