import numpy as np
import pytest

from projection import FrameComposer


def test_window_maps_min_to_0_and_max_to_255():
    composer = FrameComposer((100, 1100), (4, 4))
    out = composer.to_uint8(np.array([[100, 600, 1100, 5000]], np.uint16))
    assert out.dtype == np.uint8
    assert out.tolist() == [[0, 127, 255, 255]]


def test_constant_volume_does_not_divide_by_zero():
    assert not FrameComposer((7, 7), (2, 2)).to_uint8(np.full((2, 2), 7, np.uint8)).any()


def test_canvas_is_max_size_rounded_up_to_even():
    assert FrameComposer.canvas_for([(52, 49), (501, 401), (10, 600)]) == (502, 600)


def test_image_is_top_aligned_and_centred():
    composer = FrameComposer((0, 255), (6, 8))
    frame = composer.compose(np.full((3, 4), 255, np.uint8))
    assert frame.shape == (6, 8)
    assert (frame[:3, 2:6] == 255).all()
    assert frame.sum() == 255 * 12


def test_blank_frame_and_too_large_image():
    composer = FrameComposer((0, 255), (4, 4))
    assert composer.blank().shape == (4, 4) and not composer.blank().any()
    with pytest.raises(ValueError):
        composer.compose(np.zeros((5, 4), np.uint8))
