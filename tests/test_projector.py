import math

import numpy as np
import pytest

from conftest import decode, random_isosceles
from projection import NumbaProjector, NumpyProjector, TrapezoidPlane, TrianglePlane, plane_from_points


@pytest.fixture(params=[NumpyProjector, NumbaProjector], ids=["numpy", "numba"])
def projector(request):
    return request.param()


def reference_project(volume, plane):
    """Slow per-pixel version of ALGORITHM.md, written as plainly as possible."""
    h, w = math.floor(plane.leg_length) + 1, math.floor(plane.base_length) + 1
    v1 = (plane.b - plane.a1) / np.linalg.norm(plane.b - plane.a1)
    v2 = (plane.c - plane.a2) / np.linalg.norm(plane.c - plane.a2)
    image = np.zeros((h, w), dtype=volume.dtype)
    for y in range(h):
        a1 = plane.a1 + y * v1
        a2 = plane.a2 + y * v2
        d12 = np.linalg.norm(a2 - a1)
        dp = (a2 - a1) / max(d12, 1e-12)
        for x in range(w):
            x1 = x - (plane.base_length / 2 - d12 / 2)
            if not -0.5 <= x1 <= d12 + 0.5:
                continue
            p = np.rint(a1 + min(max(x1, 0), d12) * dp).astype(int)
            if all(0 <= p[k] < volume.shape[k] for k in range(3)):
                image[y, x] = volume[tuple(p)]
    return image


TRIANGLE = TrianglePlane((32, 5, 20), (8, 50, 20), (56, 50, 20))    # legs 51, base 48


def test_output_shape(projector):
    assert projector.output_shape(TRIANGLE) == (52, 49)
    assert projector.project(np.ones((64, 64, 64), np.uint8), TRIANGLE).shape == (52, 49)


def test_apex_and_base_corners(projector, coded_volume):
    image = projector.project(coded_volume, TRIANGLE)
    voxels = decode(image)
    inside_top = np.flatnonzero(image[0])
    assert voxels[0, inside_top].tolist() == [[32, 5, 20]]
    last = np.flatnonzero(image[-1])
    assert voxels[-1, last[0]].tolist() == [8, 50, 20]
    assert voxels[-1, last[-1]].tolist() == [56, 50, 20]


def test_every_sample_lies_on_the_plane(projector, coded_volume, rng):
    for trapezoid in (False, True):
        for _ in range(20):
            plane = plane_from_points(random_isosceles(rng, 64, trapezoid))
            image = projector.project(coded_volume, plane)
            points = decode(image[image > 0])
            normal = np.cross(plane.c - plane.b, plane.b - plane.a1)
            normal /= np.linalg.norm(normal)
            distance = np.abs((points - plane.a1) @ normal)
            assert np.all(distance <= math.sqrt(3) / 2 + 1e-9)  # rounding moves at most half a voxel diagonal


def test_shape_mask_on_constant_volume(projector):
    image = projector.project(np.full((64, 64, 64), 7, np.uint8), TRIANGLE)
    assert set(np.unique(image)) == {0, 7}
    widths = (image == 7).sum(axis=1)
    assert widths[0] == 1
    assert np.all(np.diff(widths) >= -1)           # the triangle widens towards the base
    assert widths[-1] == 49
    for y, row in enumerate(image == 7):           # each row is one centred run
        cols = np.flatnonzero(row)
        assert np.all(np.diff(cols) == 1), y
        assert abs((cols[0] + cols[-1]) / 2 - 24) <= 0.5


def test_out_of_bounds_samples_are_zero(projector):
    plane = TrianglePlane((10, 10, 5), (-20, 50, 5), (40, 50, 5))   # left part has x < 0
    image = projector.project(np.full((32, 32, 16), 9, np.uint8), plane)
    assert image[-1, 0] == 0 and image[-1, 5] == 0                 # x < 0 and y >= 32
    assert image[0, 30] == 9                                        # the apex is inside


def test_plane_fully_outside_is_black(projector):
    plane = TrianglePlane((100, 100, 100), (90, 120, 100), (110, 120, 100))
    assert not projector.project(np.full((32, 32, 32), 5, np.uint8), plane).any()


def test_axis_order(projector):
    volume = np.zeros((40, 30, 20), np.uint8)
    volume[25, 12, 7] = 200
    hit = TrianglePlane((25, 2, 7), (15, 22, 7), (35, 22, 7))       # passes through (25, 12, 7)
    miss = TrianglePlane((12, 2, 7), (2, 22, 7), (22, 22, 7))
    assert projector.project(volume, hit).max() == 200
    assert projector.project(volume, miss).max() == 0


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32])
def test_dtype_is_kept(projector, dtype):
    big = np.iinfo(dtype).max
    image = projector.project(np.full((64, 64, 64), big, dtype), TRIANGLE)
    assert image.dtype == dtype and image.max() == big


def test_fortran_and_non_contiguous_volumes(projector, coded_volume):
    expected = projector.project(coded_volume, TRIANGLE)
    np.testing.assert_array_equal(projector.project(np.asfortranarray(coded_volume), TRIANGLE), expected)
    padded = np.zeros((128, 64, 64), np.uint32)
    padded[::2] = coded_volume
    np.testing.assert_array_equal(projector.project(padded[::2], TRIANGLE), expected)


def test_matches_reference_loop(projector, rng):
    volume = rng.integers(1, 255, (48, 40, 32), dtype=np.uint8)
    for trapezoid in (False, True):
        for _ in range(10):
            plane = plane_from_points(random_isosceles(rng, 40, trapezoid))
            np.testing.assert_array_equal(projector.project(volume, plane), reference_project(volume, plane))


def test_lecturer_trapezoid_is_a_full_rectangle(projector):
    plane = TrapezoidPlane((200, 0, 0), (200, 0, 500), (200, 400, 0), (200, 400, 500))
    image = projector.project(np.full((500, 500, 500), 3, np.uint8), plane)
    assert image.shape == (501, 401)
    assert (image[:-1] == 3).all()           # the last row is z = 500, just outside the volume
    assert not image[-1].any()
