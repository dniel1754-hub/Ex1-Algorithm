# Software Design Description (SDD)
## Project: 3D Volume Plane Projection (Ex1)

## 1. Introduction
This document describes how the system is structured: its parts, how they connect, the data they exchange, where they run, and why.

It sits in this chain of documents:

| Document | Question it answers |
|---|---|
| [SRS.md](SRS.md) | What the system must do, and its use cases |
| **SDD.md** (this document) | How the system is structured |
| [ALGORITHM.md](ALGORITHM.md) | How the projection component is built. This is the detailed design (EDD) of `Projector` |
| [TESTING.md](TESTING.md) | How we test (STP), and the test cases (STD) |
| [docs/adr/](docs/adr/) | Why each major decision was taken |

Diagrams are written in Mermaid ("diagrams as code"), so GitHub renders them and they are reviewed in pull requests like the code.

## 2. Context
The system is a command-line program that runs on one machine. It reads two files and writes one.

```mermaid
flowchart LR
    user(["👤 User"]) -- "python Ex0.py vol.nrrd planes.csv out.mp4" --> sys["Plane projection system<br/>(Ex0.py + projection package)"]
    nrrd[("volume.nrrd<br/>3D raster")] --> sys
    csv[("planes.csv<br/>one plane per row")] --> sys
    sys --> mp4[("out.mp4<br/>one frame per row")]
    sys -- "warnings, errors, summary" --> user
```

## 3. Decomposition

### 3.1 Components
```mermaid
flowchart TB
    cli["Ex0.py<br/>CLI and orchestration"]
    subgraph projection ["projection package"]
        reader["PlaneReader<br/>plane_reader.py"]
        geometry["TrianglePlane / TrapezoidPlane<br/>geometry.py"]
        volume["Volume<br/>volume.py"]
        projector["Projector<br/>projector.py + _kernel.py"]
        composer["FrameComposer<br/>frame_composer.py"]
        writer["VideoWriter<br/>video_writer.py"]
    end
    cli --> reader --> geometry
    cli --> volume
    cli --> projector
    cli --> composer
    cli --> writer
    projector --> geometry
    volume -. pynrrd .-> ext1[("NRRD file")]
    writer -. "imageio-ffmpeg" .-> ext2[("MP4 file")]
    projector -. numba .-> ext3["compiled kernel"]
```

| Component | Responsibility | Depends on |
|---|---|---|
| `Ex0.py` | Parses arguments, wires the components together, reports warnings and errors, and maps failures to exit codes | All components |
| `PlaneReader` | Turns CSV lines into `PlaneRecord`s, each holding either a valid plane or an error | `geometry` |
| `TrianglePlane`, `TrapezoidPlane` | Hold the four scan points `a1, b, a2, c` and validate them against SRS FR-3 | NumPy |
| `Volume` | Loads the NRRD as `data[x, y, z]` and computes the intensity window | pynrrd |
| `Projector` | Computes the image E of a plane through the volume (detailed in ALGORITHM.md) | `geometry`, Numba (optional) |
| `FrameComposer` | Maps E to 8 bits and places it on a fixed, even-sized canvas | NumPy |
| `VideoWriter` | Encodes frames to H.264 MP4 | imageio-ffmpeg |

Each component has one reason to change. Only `Ex0.py` knows about files and exit codes. `Projector` takes a plain NumPy array, so it can be tested without any files (NFR-4).

### 3.2 Classes
```mermaid
classDiagram
    direction LR
    class Plane {
        <<abstract>>
        +a1, b, a2, c : ndarray
        +leg_length() float
        +base_length() float
        +top_length() float
        +validate()*
    }
    class TrianglePlane {
        +TrianglePlane(a, b, c)
        +validate()
    }
    class TrapezoidPlane {
        +TrapezoidPlane(a1, b, a2, c)
        +validate()
    }
    class PlaneRecord {
        +frame : int
        +line : int
        +plane : Plane | None
        +error : str | None
        +is_valid() bool
    }
    class PlaneReader {
        +read(path) list~PlaneRecord~
        +parse_lines(lines) list~PlaneRecord~
    }
    class Volume {
        +data : ndarray
        +shape() tuple
        +dtype() dtype
        +window() tuple
        +load(path)$ Volume
    }
    class Projector {
        <<abstract>>
        +output_shape(plane)$ tuple
        +project(volume, plane)* ndarray
        +warm_up(volume)
    }
    class NumbaProjector {
        +project(volume, plane) ndarray
        +warm_up(volume)
    }
    class NumpyProjector {
        +project(volume, plane) ndarray
    }
    class FrameComposer {
        +canvas_shape : tuple
        +canvas_for(shapes)$ tuple
        +to_uint8(image) ndarray
        +compose(image) ndarray
        +blank() ndarray
    }
    class VideoWriter {
        +frames_written : int
        +write(frame)
    }
    Plane <|-- TrianglePlane
    Plane <|-- TrapezoidPlane
    Projector <|-- NumbaProjector
    Projector <|-- NumpyProjector
    PlaneReader ..> PlaneRecord : creates
    PlaneRecord o-- "0..1" Plane
    Projector ..> Plane : reads
    Projector ..> Volume : samples data
```

- **Two hierarchies, each a strategy.** `Plane` hides whether the input was 3 or 4 points: a triangle is stored as a trapezoid with `a1 == a2`, so the projector has a single code path. `Projector` hides which implementation runs. `default_projector()` picks Numba when it is installed and NumPy otherwise. Callers depend only on the abstract classes.
- **Errors are values, not crashes.** An invalid row becomes a `PlaneRecord` with an `error` message instead of an exception that stops the run. This is how FR-6 keeps "frame i matches row i". `InvalidPlaneError` and `VolumeLoadError` are used only inside the package, and at the CLI boundary.

## 4. Dynamic view: one run of `Ex0.py`
```mermaid
sequenceDiagram
    actor User
    participant CLI as Ex0.py
    participant Vol as Volume
    participant Rd as PlaneReader
    participant Pr as Projector
    participant Co as FrameComposer
    participant Wr as VideoWriter
    User->>CLI: python Ex0.py vol.nrrd planes.csv out.mp4
    CLI->>Vol: load(vol.nrrd)
    Vol-->>CLI: volume
    CLI->>Rd: read(planes.csv)
    Rd-->>CLI: records (valid and invalid)
    CLI-->>User: warning for each invalid record
    CLI->>Pr: default_projector(), warm_up(volume.data)
    CLI->>Co: FrameComposer(volume.window, canvas_for(shapes))
    CLI->>Wr: open out.mp4
    loop every record, in CSV order
        alt record is valid
            CLI->>Pr: project(volume.data, plane)
            Pr-->>CLI: image E
            CLI->>Co: compose(E)
            Co-->>CLI: 8-bit frame
        else record is invalid
            CLI->>Co: blank()
            Co-->>CLI: black frame
        end
        CLI->>Wr: write(frame)
    end
    CLI->>Wr: close
    CLI-->>User: summary, exit code 0
```

**Error handling at the boundary.** `Ex0.main` converts failures into exit codes:
- `VolumeLoadError`, a missing input file or a missing output folder → message on stderr and exit code 1.
- `OSError` while writing the video → "cannot write output" and exit code 1.
- Wrong number of arguments → usage line and exit code 2.

No stack trace reaches the user for an expected failure (NFR-2).

## 5. Data, libraries and runtime
- **File formats** (NRRD, the plane CSV, MP4) are specified in [SRS FR-1, FR-2 and FR-5](SRS.md#2-functional-requirements). The image E is described in [ALGORITHM.md](ALGORITHM.md).
- **Volume in memory:** pynrrd loads the NRRD in Fortran index order, so `data[x, y, z]` matches the CSV coordinates with no copy or transpose. It is held once: 125 MB for 500³ uint8, up to 4.3 GB for 1023³ uint32.
- **Libraries:** NumPy, Numba (optional), pynrrd for NRRD input, imageio with imageio-ffmpeg for H.264 MP4 output at 10 FPS, and pytest for the tests. Versions are in `requirements.txt`.
- **Runtime:** one Python process, with no network and no server. Numba spreads rows across all CPU cores and caches the compiled kernel in `projection/__pycache__`, so only the first run pays the roughly 1 s compile time.

## 6. Design rationale
Major decisions and the alternatives we rejected are recorded in [docs/adr/](docs/adr/).
