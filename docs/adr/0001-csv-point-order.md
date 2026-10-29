# ADR-0001: 4-point CSV rows are in leg order `a1, b, a2, c`

- **Status:** Accepted
- **Date:** 2026-10-26
- **Requirements:** SRS FR-2, FR-3

## Context
The assignment defines a trapezoid by "two vectors on the same plane with the same length: a′→b and a″→c", but it never says in which order the four points appear in a CSV row. The lecturer's sample CSV has two 4-point rows:

| Row | As `a1, a2, b, c` | As `a1, b, a2, c` |
|---|---|---|
| 2 | Legs 400 and 400, bases 500 and 500: valid | Legs 500 and 500, bases 400 and 400: valid |
| 4 | Legs **300 and 400**: invalid | Legs **502.49 and 502.49**, bases 300 ≤ 400: valid |

## Decision
We read a 4-point row as the two legs one after the other: `a1, b, a2, c`. The legs are `a1→b` and `a2→c`, and `a1–a2` is the short base.

## Consequences
- The lecturer's row 4 is an isosceles trapezoid, which is presumably what was intended.
- The order matches the class dataset (`edge_cases.csv` documents "a′, b, a″, c"), so our tool and our classmates' tools read the same files the same way.
- TC-05 is a regression test that fails if the order is ever changed by accident.

## Alternatives considered
- **`a1, a2, b, c`** (both top points, then both bottom points): rejected, because it makes the lecturer's row 4 invalid.
- **Detect the order automatically**, by trying both and keeping the valid one: rejected. Rectangles are valid in both orders but produce different images, so the result would be ambiguous.
