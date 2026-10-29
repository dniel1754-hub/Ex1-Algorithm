import pytest

from conftest import LECTURER_CSV
from projection import PlaneReader, TrapezoidPlane, TrianglePlane

HEADER = "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4"
TRIANGLE = "3,0,0,0,-30,40,0,30,40,0,,,"


def parse(*lines):
    return PlaneReader().parse_lines(list(lines))


def test_lecturer_example():
    records = PlaneReader().read(LECTURER_CSV)
    assert [r.frame for r in records] == [1, 2, 3, 4]
    assert [r.is_valid for r in records] == [True, True, False, True]
    assert isinstance(records[0].plane, TrianglePlane)
    assert isinstance(records[1].plane, TrapezoidPlane)
    assert "legs differ" in records[2].error


def test_header_blank_and_comment_lines_are_skipped():
    records = parse(HEADER, "", "# a comment", TRIANGLE, "   ", "#another", TRIANGLE)
    assert [(r.frame, r.line) for r in records] == [(1, 4), (2, 7)]
    assert all(r.is_valid for r in records)


def test_file_without_header():
    assert parse(TRIANGLE)[0].is_valid


def test_negative_and_float_coordinates():
    record = parse(HEADER, "3,1.5,-2.25,0,-28.5,37.75,0,31.5,37.75,0")[0]
    assert record.is_valid
    assert record.plane.a1.tolist() == [1.5, -2.25, 0]


@pytest.mark.parametrize("row, message", [
    ("5,0,0,0,1,1,1,2,2,2,3,3,3", "point count"),
    ("abc,0,0,0,1,1,1,2,2,2", "point count"),
    ("3,0,0,0,-30,40,0,30,40", "expected 9 coordinates"),
    ("3,0,0,0,-30,40,0,30,,0", "expected 9 coordinates"),
    ("3,0,0,0,-30,40,0,30,40,x", "non-numeric"),
    ("3,0,0,0,-30,40,0,30,40,0,1,2,3", "unexpected values"),
    ("4,0,0,0,-30,40,0,30,40,0,,,", "expected 12 coordinates"),
])
def test_malformed_rows_are_invalid_and_parsing_continues(row, message):
    records = parse(HEADER, row, TRIANGLE)
    assert len(records) == 2
    assert not records[0].is_valid and message in records[0].error
    assert records[1].is_valid and records[1].frame == 2
