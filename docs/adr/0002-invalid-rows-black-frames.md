# ADR-0002: Invalid rows give a warning and a black frame

- **Status:** Accepted
- **Date:** 2026-10-26
- **Requirements:** SRS FR-6, NFR-2

## Context
The assignment requires "a frame for each corresponding plane coordinate as presented in the csv file (in the list order)". Real input contains bad rows. The lecturer's own sample has a non-isosceles triangle (row 3), and the class `edge_cases.csv` has malformed numbers, infinities, crossed legs and oversized planes. We have to decide what one bad row does to the run.

## Decision
- A row that is malformed or fails validation produces a **warning** on stderr, with the frame number, line number and reason, and an **all-black frame** in its position. The run continues.
- The run fails, with exit code 1, only when no row at all is valid.
- A valid plane that misses the volume is not an error. It simply projects to black, with no warning.

## Consequences
- **Frame i always corresponds to CSV row i**, so the video can be lined up with the CSV without counting skipped rows.
- One bad row never loses the other frames.
- A black frame is ambiguous on its own: it can mean "invalid" or "valid but outside the volume". The warning tells the two apart.
- In code, invalid rows are values (`PlaneRecord.error`), not exceptions that escape the reader (SDD §3.2).

## Alternatives considered
- **Skip invalid rows:** rejected. Frame numbers would no longer match row numbers.
- **Stop at the first invalid row:** rejected. It's fragile, and the lecturer's own sample would fail.
- **Draw doubtful planes anyway, with a warning** (the classmate's design for unequal legs): rejected. The spec's EPS rule is explicit, and drawing a non-isosceles shape would be a guess about what was meant.
