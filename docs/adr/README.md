# Architecture Decision Records

Each file records one decision: the context, what we decided, its consequences, and the alternatives we rejected. A decision is never edited away. If it changes, add a new ADR that supersedes the old one, and update the old one's status.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-csv-point-order.md) | 4-point CSV rows are in leg order `a1, b, a2, c` | Accepted |
| [0002](0002-invalid-rows-black-frames.md) | Invalid rows give a warning and a black frame | Accepted |
| [0003](0003-voxel-coordinates.md) | Coordinates are voxel indices; NRRD spacing is ignored | Accepted |
| [0004](0004-half-pixel-margin.md) | Half-pixel margin, with samples clamped onto the row | Accepted |
| [0005](0005-numba-projector.md) | Numba-compiled projector, with a NumPy fallback | Accepted |

**Template for a new ADR** (`NNNN-short-title.md`): Status · Date · Context · Decision · Consequences · Alternatives considered.
