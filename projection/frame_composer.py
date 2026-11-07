"""Turns projected images into fixed-size 8-bit video frames (SRS FR-5, FR-6)."""
from __future__ import annotations

import numpy as np

# 3x5 bitmap glyphs (each 15-bit integer encodes 5 rows of 3 bits, MSB at top-left).
_GLYPHS = {
    "0": 0b111_101_101_101_111, "1": 0b010_110_010_010_111, "2": 0b111_001_111_100_111,
    "3": 0b111_001_111_001_111, "4": 0b101_101_111_001_001, "5": 0b111_100_111_001_111,
    "6": 0b111_100_111_101_111, "7": 0b111_001_001_001_001, "8": 0b111_101_111_101_111,
    "9": 0b111_101_111_001_111, "E": 0b111_100_111_100_111, "R": 0b110_101_110_101_101,
    " ": 0,
}


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

    def error_frame(self, frame_no: int | None = None) -> np.ndarray:
        """Return a black frame marked with a diagonal cross and 'ERR <frame_no>' (SRS FR-6)."""
        frame = self.blank()
        h, w = self.canvas_shape
        thickness = max(1, min(h, w) // 160)
        ys = np.arange(h)
        xs = np.rint(ys * (w - 1) / max(h - 1, 1)).astype(int)
        for d in range(-thickness, thickness + 1):
            frame[ys, np.clip(xs + d, 0, w - 1)] = 200
            frame[ys, np.clip((w - 1 - xs) + d, 0, w - 1)] = 200
        xs_all = np.arange(w)
        ys_diag = np.rint(xs_all * (h - 1) / max(w - 1, 1)).astype(int)
        for d in range(-thickness, thickness + 1):
            frame[np.clip(ys_diag + d, 0, h - 1), xs_all] = 200
            frame[np.clip((h - 1 - ys_diag) + d, 0, h - 1), xs_all] = 200
        frame[:thickness, :] = frame[-thickness:, :] = 200
        frame[:, :thickness] = frame[:, -thickness:] = 200

        if frame_no is not None:
            label = _render_text(f"ERR {frame_no}")
            scale = min(h // 12, w // (label.shape[1] + 4), 6)
            if scale >= 1:
                scaled = np.repeat(np.repeat(label, scale, axis=0), scale, axis=1)
                lh, lw = scaled.shape
                top = max(thickness + 1, (h - lh) // 6)
                left = (w - lw) // 2
                pad = max(1, scale)
                frame[max(0, top - pad):min(h, top + lh + pad),
                      max(0, left - pad):min(w, left + lw + pad)] = 0
                frame[top:top + lh, left:left + lw] = scaled
        return frame


def _render_text(text: str) -> np.ndarray:
    """Render uppercase text using the 3x5 bitmap font into a uint8 array of 0 and 255."""
    cols = []
    for ch in text:
        bits = _GLYPHS.get(ch, 0)
        glyph = np.array([[(bits >> (14 - 3 * r - c)) & 1 for c in range(3)] for r in range(5)], dtype=np.uint8)
        cols.append(glyph * 255)
        cols.append(np.zeros((5, 1), dtype=np.uint8))
    return np.hstack(cols[:-1]) if cols else np.zeros((5, 0), dtype=np.uint8)
