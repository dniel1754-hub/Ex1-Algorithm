# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, Cursor, and others) working in this repository. People should start with [README.md](README.md).

## What this is
This is Ex1 of Intro2SE: project a 3D NRRD volume onto planes (isosceles triangles or trapezoids) listed in a CSV, and write one MP4 frame per row:

```
python Ex0.py <file.nrrd> <file.csv> <file.mp4>
```

The course grades **design and documentation** as much as code. Keep the documents true.

## Read before changing anything
| Document | Read it when |
|---|---|
| [SRS.md](SRS.md) | You change behaviour. Requirements FR-1…7 and NFR-1…4, use case UC-01, and the traceability matrix in Appendix A |
| [SDD.md](SDD.md) | You add, remove or rewire a component or class |
| [ALGORITHM.md](ALGORITHM.md) | You touch `projection/projector.py` or `projection/_kernel.py` |
| [TESTING.md](TESTING.md) | You add or change tests. Test cases are numbered TC-01…TC-47 |
| [docs/adr/](docs/adr/) | You are tempted to change one of the recorded decisions |

## Commands
Use the local virtual environment `.venv` if it exists (`.venv/Scripts/python` on Windows, `.venv/bin/python` elsewhere).

```bash
pip install -r requirements.txt
python -m pytest                              # all tests, ~5 s; NRRD-based tests skip if data/*.nrrd is missing
python benchmarks/bench_projection.py         # FPS on 500³; must exit 0 (≥ 30 FPS)
python Ex0.py data/MRHead_1.nrrd data/head.csv out.mp4
```

The class NRRDs are not committed. Their download link is in the README's Dataset section.

## Rules that are easy to break
- **4-point rows are `a1, b, a2, c`** (ADR-0001). Don't "fix" this to `a1, a2, b, c`, because TC-05 exists to catch exactly that.
- **Frame i is CSV row i.** Invalid rows give a warning and a black frame. They are never skipped (ADR-0002).
- **Coordinates are voxel indices** into `data[x, y, z]`, loaded with pynrrd's default Fortran order (ADR-0003). Don't transpose the volume.
- **The two projectors must stay bit-identical.** If you change the arithmetic in one, change the other in the same order. TC-30 compares both against a reference loop.
- **No per-pixel Python loops in the hot path.** Use the Numba kernel or NumPy operations. Re-run the benchmark after touching the projector.
- **The CLI owns I/O and exit codes.** Package code raises `InvalidPlaneError` or `VolumeLoadError`, or returns records. Only `Ex0.py` prints and exits.
- **Don't commit** `data/*.nrrd`, `.venv/` or ad-hoc MP4s. Only `experiment/*.mp4` is committed (see `.gitignore`).

## Definition of done
A change is done when, **in the same pull request**:
1. `python -m pytest` passes, and the benchmark still exits 0 if the projector was touched.
2. New behaviour has a test, and the test has a TC ID in TESTING.md §5, with the requirement it verifies.
3. If a requirement, component or decision changed, update the SRS (including the Appendix A traceability row), SDD and ADRs, or add a new ADR. Never silently edit a past decision.
4. The README stays accurate: commands, layout, progress and results.

## Workflow
- Branch from the latest work and open a pull request for review. Your teammate reviews before anything reaches `main`. Don't push to `main` directly.
- Prefer small, logical commits. The course asks for frequent commits.
- Before reporting work as finished, run the tests and say exactly what was and wasn't verified.
