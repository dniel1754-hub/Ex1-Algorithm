# ADR-0001: 4-point CSV rows are in leg order `a1, b, a2, c`

- **Status:** Accepted
- **Date:** 2026-10-26
- **Requirements:** SRS FR-2, FR-3

## Context
The assignment body defines a trapezoid by "two vectors on the same plane with the same length: a′→b and a″→c", while the Q&A section names the four vertices as `(a1, a2, b, c)` when listing the geometric conditions (`|dist(a1,b) - dist(a2,c)| < EPS`, `dist(a1,a2) <= dist(b,c)`, and `a1→b` and `a2→c` coplanar). Neither specifies whether the CSV columns list the two top vertices first (`a1, a2, b, c`) or the two leg vectors one after the other (`a1, b, a2, c`).

The lecturer's sample CSV (`data/lecturer_example.csv`) has two 4-point rows:

| Row | As `a1, a2, b, c` | As `a1, b, a2, c` |
|---|---|---|
| 2 | Legs 400 and 400, bases 500 and 500: valid | Legs 500 and 500, bases 400 and 400: valid |
| 4 | Legs **300 and 400**: invalid | Legs **502.49 and 502.49**, bases 300 ≤ 400: valid |

## Decision
We treat the Q&A's `(a1, a2, b, c)` as mathematical vertex names, and read a 4-point CSV row as the two leg vectors one after the other: `a1, b, a2, c`. The legs are `a1→b` and `a2→c`, and `a1–a2` is the short base.

## Consequences
- The lecturer's row 4 is a valid isosceles trapezoid, which is what the sample CSV intended.
- The order matches the class dataset (`edge_cases.csv` explicitly documents `4 for a trapezoid a', b, a'', c`), so our tool and our classmates' tools read the same files the same way.
- TC-05 is a regression test that fails if the order is ever changed by accident.

## Alternatives considered
- **`a1, a2, b, c`** (both top points, then both bottom points): rejected, because it makes the lecturer's row 4 invalid.
- **Detect the order automatically**, by trying both and keeping the valid one: rejected. Rectangles are valid in both orders but produce different images, so the result would be ambiguous.
