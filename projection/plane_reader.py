"""Reads the plane CSV (SRS FR-2): one plane per row, invalid rows kept as records."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .geometry import InvalidPlaneError, Plane, plane_from_points


@dataclass(frozen=True)
class PlaneRecord:
    """One data row of the CSV. Exactly one of `plane` / `error` is set."""
    frame: int          # 1-based frame number (= data row number)
    line: int           # 1-based line number in the file
    plane: Plane | None = None
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.plane is not None


class PlaneReader:
    """Parses `n, x1,y1,z1, ..., x4,y4,z4` rows; blank and `#` lines are skipped."""

    def read(self, path: str | Path) -> list[PlaneRecord]:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return self.parse_lines(f)

    def parse_lines(self, lines) -> list[PlaneRecord]:
        records: list[PlaneRecord] = []
        header_seen = False
        for line_no, cells in enumerate(csv.reader(lines), start=1):
            cells = [cell.strip() for cell in cells]
            if not any(cells) or cells[0].startswith("#"):
                continue
            if not header_seen:
                header_seen = True
                if not _is_number(cells[0]):
                    continue
            records.append(self._parse_row(len(records) + 1, line_no, cells))
        return records

    @staticmethod
    def _parse_row(frame: int, line_no: int, cells: list[str]) -> PlaneRecord:
        try:
            return PlaneRecord(frame, line_no, plane=plane_from_points(_points(cells)))
        except InvalidPlaneError as e:
            return PlaneRecord(frame, line_no, error=str(e))


def _is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def _points(cells: list[str]) -> list[list[float]]:
    if not _is_number(cells[0]) or float(cells[0]) not in (3, 4):
        raise InvalidPlaneError(f"point count must be 3 or 4, got {cells[0]!r}")
    n = int(float(cells[0]))
    coords, extra = cells[1:1 + 3 * n], cells[1 + 3 * n:]
    if len(coords) < 3 * n or not all(coords):
        raise InvalidPlaneError(f"expected {3 * n} coordinates for {n} points")
    if any(extra):
        raise InvalidPlaneError(f"unexpected values after {n} points: {[e for e in extra if e]}")
    if not all(_is_number(v) for v in coords):
        raise InvalidPlaneError(f"non-numeric coordinate in {coords}")
    values = [float(v) for v in coords]
    return [values[i:i + 3] for i in range(0, 3 * n, 3)]
