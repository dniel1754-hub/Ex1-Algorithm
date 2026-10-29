"""Turns projected images into fixed-size 8-bit video frames (SRS FR-5)."""
from __future__ import annotations

import numpy as np


class FrameComposer:
    """Maps intensities to 0..255 with one shared window and pads onto a fixed canvas."""

    def __init__(self, window: tuple[float, float], canvas_shape: tuple[int, int]):
        lo, hi = window
        self.lo = lo
        self.scale = 255.0 / (hi - lo) if hi > lo else 0.0
        self.canvas_shape = canvas_shape

    @staticmethod
    def canvas_for(shapes) -> tuple[int, int]:
        """Smallest even-sized canvas that holds every image shape (H.264 needs even sizes)."""
        shapes = list(shapes)
        h = max((s[0] for s in shapes), default=2)
        w = max((s[1] for s in shapes), default=2)
        return h + h % 2, w + w % 2

    def to_uint8(self, image: np.ndarray) -> np.ndarray:
        scaled = (image.astype(np.float32) - self.lo) * self.scale
        return np.clip(scaled, 0, 255).astype(np.uint8)

    def compose(self, image: np.ndarray) -> np.ndarray:
        """Place the image top-aligned and horizontally centred on a black canvas."""
        h, w = image.shape
        canvas_h, canvas_w = self.canvas_shape
        if h > canvas_h or w > canvas_w:
            raise ValueError(f"image {image.shape} does not fit canvas {self.canvas_shape}")
        frame = self.blank()
        left = (canvas_w - w) // 2
        frame[:h, left:left + w] = self.to_uint8(image)
        return frame

    def blank(self) -> np.ndarray:
        return np.zeros(self.canvas_shape, dtype=np.uint8)
