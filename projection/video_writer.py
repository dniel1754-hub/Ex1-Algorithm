"""MP4 output (SRS FR-5)."""
from __future__ import annotations

from pathlib import Path

import numpy as np


class VideoWriter:
    """Writes grayscale uint8 frames to an H.264 MP4. Use as a context manager."""

    def __init__(self, path: str | Path, fps: float = 10):
        self.path = Path(path)
        self.fps = fps
        self._writer = None
        self.frames_written = 0

    def __enter__(self) -> "VideoWriter":
        import imageio.v2 as imageio

        self._writer = imageio.get_writer(
            str(self.path), fps=self.fps, codec="libx264", pixelformat="yuv420p",
            macro_block_size=2, quality=8)
        return self

    def write(self, frame: np.ndarray) -> None:
        self._writer.append_data(frame)
        self.frames_written += 1

    def __exit__(self, *exc) -> None:
        self._writer.close()
