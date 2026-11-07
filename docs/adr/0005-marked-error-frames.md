# ADR-0005: Invalid rows produce a marked error frame on a black canvas

- **Status:** Accepted (supersedes [ADR-0002](0002-invalid-rows-black-frames.md))
- **Date:** 2026-11-07
- **Requirements:** SRS FR-5, FR-6, NFR-2

## Context
In the assignment's Q&A, the lecturer specifies:
- If the set of 3 or 4 points is not valid (with `EPS = 0.001`), an exception should be raised.
- In the demo (`Ex0.py`), the output video should include an **"Error frame"** — for example, a black frame with some marking regarding the wrong point set — while all valid planes produce their projected frames.

Under [ADR-0002](0002-invalid-rows-black-frames.md), invalid rows were written as plain unmarked black frames (`FrameComposer.blank()`). As ADR-0002 noted, an unmarked black frame in the video could not be visually distinguished from a valid plane that happens to lie completely outside the volume (such as frame 6 in `data/edge_cases.csv`).

## Decision
- In `geometry.py`, invalid point sets continue to raise `InvalidPlaneError` (caught by `PlaneReader` into `PlaneRecord.error`).
- In `Ex0.py`, each invalid row still prints a warning on stderr and writes a frame in its CSV position, but now uses `FrameComposer.error_frame(frame_no)` instead of `blank()`.
- `FrameComposer.error_frame(frame_no)` returns a black canvas marked with a grey border, a diagonal cross (`X`), and — whenever the canvas is large enough — a crisp bitmap label `ERR <frame_no>` near the top.
- A valid plane that misses the volume still projects to an unmarked all-black frame with no warning.
- If no row in the CSV is valid, the demo still exits with code 1, because no valid plane exists to define the canvas dimensions.

## Consequences
- Satisfies the lecturer's Q&A requirement for a visibly marked "Error frame" on a black background.
- Viewers watching the MP4 can immediately tell an invalid CSV row (`X` + `ERR <frame_no>`) apart from a valid plane outside the volume (unmarked black), and can see which row number failed directly in the frame.
- Requires no external font or imaging dependency: the cross and 3×5 bitmap glyphs are drawn with pure NumPy operations in `frame_composer.py`.

## Alternatives considered
- **Plain unmarked black frame (ADR-0002):** superseded, because it lacks the visual marking requested in the Q&A and is indistinguishable from out-of-bounds planes.
- **Pillow / OpenCV text rendering:** rejected, to avoid adding a new library dependency for a simple diagnostic label.
