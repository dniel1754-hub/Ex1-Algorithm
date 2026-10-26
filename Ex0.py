"""Demo: python Ex0.py <file.nrrd> <file.csv> <file.mp4>

Projects the volume onto every plane in the CSV and writes one frame per row.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from projection import FrameComposer, PlaneReader, VideoWriter, Volume, VolumeLoadError, default_projector

USAGE = "usage: python Ex0.py <file.nrrd> <file.csv> <file.mp4>"


def run(nrrd_path: str, csv_path: str, mp4_path: str) -> int:
    for path in (nrrd_path, csv_path):
        if not Path(path).is_file():
            return _fail(f"file not found: {path}")
    if not Path(mp4_path).resolve().parent.is_dir():
        return _fail(f"output folder does not exist: {Path(mp4_path).parent}")

    volume = Volume.load(nrrd_path)
    records = PlaneReader().read(csv_path)
    for r in records:
        if not r.is_valid:
            print(f"warning: frame {r.frame} (line {r.line}): invalid plane, writing a black frame: {r.error}",
                  file=sys.stderr)
    valid = [r for r in records if r.is_valid]
    if not valid:
        return _fail(f"no valid planes in {csv_path}")

    projector = default_projector()
    projector.warm_up(volume.data)
    canvas = FrameComposer.canvas_for(projector.output_shape(r.plane) for r in valid)
    composer = FrameComposer(volume.window, canvas)

    projection_time = 0.0
    with VideoWriter(mp4_path) as video:
        for r in records:
            if not r.is_valid:
                video.write(composer.blank())
                continue
            start = time.perf_counter()
            image = projector.project(volume.data, r.plane)
            projection_time += time.perf_counter() - start
            video.write(composer.compose(image))

    fps = len(valid) / projection_time if projection_time > 0 else float("inf")
    print(f"volume {volume.shape} {volume.dtype}: wrote {video.frames_written} frames "
          f"({len(valid)} projected, {len(records) - len(valid)} black) of {canvas[1]}x{canvas[0]} "
          f"to {mp4_path}; projection {fps:.0f} FPS ({type(projector).__name__})")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        return run(*argv)
    except VolumeLoadError as e:
        return _fail(str(e))
    except OSError as e:
        return _fail(f"cannot write output: {e}")


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
