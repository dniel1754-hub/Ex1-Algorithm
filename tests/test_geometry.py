import numpy as np
import pytest

from conftest import random_isosceles
from projection import InvalidPlaneError, TrapezoidPlane, TrianglePlane, plane_from_points

LECTURER_ROWS = {
    1: [(200, 200, 0), (0, 200, 400), (400, 200, 400)],
    2: [(200, 0, 0), (200, 0, 500), (200, 400, 0), (200, 400, 500)],
    3: [(200, 200, -30), (-50, 200, 400), (400, 250, 400)],
    4: [(200, 50, 0), (200, 0, 500), (200, 350, 0), (200, 400, 500)],
}


def test_lecturer_triangle_is_valid():
    plane = plane_from_points(LECTURER_ROWS[1])
    assert isinstance(plane, TrianglePlane)
    assert plane.leg_length == pytest.approx(447.2136, abs=1e-4)
    assert plane.base_length == pytest.approx(400)


def test_lecturer_rectangle_is_valid():
    plane = plane_from_points(LECTURER_ROWS[2])
    assert isinstance(plane, TrapezoidPlane)
    assert (plane.leg_length, plane.top_length, plane.base_length) == pytest.approx((500, 400, 400))


def test_lecturer_non_isosceles_triangle_is_invalid():
    with pytest.raises(InvalidPlaneError, match="legs differ"):
        plane_from_points(LECTURER_ROWS[3])


def test_lecturer_row_4_is_valid_in_leg_order():
    plane = plane_from_points(LECTURER_ROWS[4])
    assert plane.leg_length == pytest.approx(502.4938, abs=1e-4)
    assert (plane.top_length, plane.base_length) == pytest.approx((300, 400))


def test_lecturer_row_4_in_wrong_order_is_invalid():
    a1, b, a2, c = LECTURER_ROWS[4]
    with pytest.raises(InvalidPlaneError, match="legs differ"):
        TrapezoidPlane(a1, a2, b, c)


@pytest.mark.parametrize("delta, valid", [(0.0005, True), (0.002, False)])
def test_leg_difference_against_eps(delta, valid):
    stretch = (50 + delta) / 50
    points = [(0, 0, 0), (-30, 40, 0), (30 * stretch, 40 * stretch, 0)]  # legs 50 and 50 + delta
    if valid:
        plane_from_points(points)
    else:
        with pytest.raises(InvalidPlaneError):
            plane_from_points(points)


def test_trapezoid_with_longer_top_is_invalid():
    with pytest.raises(InvalidPlaneError, match="longer than bottom"):
        TrapezoidPlane((0, 0, 0), (10, 10, 0), (30, 0, 0), (20, 10, 0))


def test_trapezoid_with_crossed_legs_is_invalid():
    a1, b, a2, c = LECTURER_ROWS[2]
    with pytest.raises(InvalidPlaneError, match="legs cross"):
        TrapezoidPlane(a2, b, a1, c)   # a1 and a2 swapped: still equal legs, but a bow tie


def test_oversized_plane_is_invalid():
    with pytest.raises(InvalidPlaneError, match="too large"):
        TrianglePlane((0, 0, 0), (-2000, 3000, 0), (2000, 3000, 0))


def test_trapezoid_off_plane_is_invalid():
    with pytest.raises(InvalidPlaneError, match="not coplanar"):
        TrapezoidPlane((0, 0, 0), (-5, 20, 0), (10, 0, 3), (15, 20, 3))  # equal legs, a2 lifted off


@pytest.mark.parametrize("points", [
    [(1, 2, 3), (1, 2, 3), (1, 2, 3)],               # all identical
    [(0, 0, 0), (0, 0, 0), (0, 0, 0)],
    [(0, 0, 0), (5, 5, 5), (5, 5, 5)],                # b == c
    [(0, 0, 0), (-1, 0, 0), (1, 0, 0)],               # apex on the base line
    [(0, 0, 0), (1, 1, 1)],                           # too few points
])
def test_degenerate_shapes_are_invalid(points):
    with pytest.raises(InvalidPlaneError):
        plane_from_points(points)


def test_non_finite_coordinates_are_invalid():
    with pytest.raises(InvalidPlaneError):
        plane_from_points([(0, 0, float("nan")), (1, 0, 0), (0, 1, 0)])


def test_random_isosceles_shapes_are_valid(rng):
    for trapezoid in (False, True):
        for _ in range(50):
            plane_from_points(random_isosceles(rng, 100, trapezoid))


def test_triangle_is_trapezoid_with_zero_top():
    plane = TrianglePlane((0, 0, 0), (-3, 4, 0), (3, 4, 0))
    np.testing.assert_array_equal(plane.a1, plane.a2)
    assert plane.top_length == 0
