import imageio.v2 as imageio
import nrrd
import numpy as np
import pytest

import Ex0
from projection import FrameComposer, NumpyProjector, PlaneReader, Volume, VolumeLoadError

PLANES = "\n".join([
    "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4",
    "3,32,5,20,8,50,20,56,50,20,,,",
    "3,32,5,20,8,50,20,56,51,20,,,",          # invalid: legs differ
    "4,20,5,30,8,50,30,44,5,30,56,50,30",
    "# trailing comment",
])


@pytest.fixture
def volume_file(tmp_path, coded_volume):
    path = tmp_path / "coded.nrrd"
    nrrd.write(str(path), coded_volume)
    return path


def test_nrrd_round_trip_keeps_axis_order_and_type(volume_file, coded_volume):
    volume = Volume.load(volume_file)
    assert volume.shape == (64, 64, 64) and volume.dtype == np.uint32
    np.testing.assert_array_equal(volume.data, coded_volume)
    assert volume.data[3, 2, 1] == 3 + 64 * 2 + 4096 * 1
    assert volume.window == (0, 63 + 64 * 63 + 4096 * 63)


def test_load_errors(tmp_path):
    with pytest.raises(VolumeLoadError, match="not found"):
        Volume.load(tmp_path / "missing.nrrd")
    bad = tmp_path / "bad.nrrd"
    bad.write_text("this is not an nrrd file")
    with pytest.raises(VolumeLoadError, match="cannot read"):
        Volume.load(bad)
    with pytest.raises(VolumeLoadError, match="3D"):
        Volume(np.zeros((4, 4), np.uint8))


def test_demo_writes_one_frame_per_row(tmp_path, volume_file, capsys):
    csv_path = tmp_path / "planes.csv"
    csv_path.write_text(PLANES)
    mp4 = tmp_path / "out.mp4"

    assert Ex0.main([str(volume_file), str(csv_path), str(mp4)]) == 0

    out = capsys.readouterr()
    assert "frame 2" in out.err and "legs differ" in out.err
    with imageio.get_reader(str(mp4)) as reader:   # list(reader) fails: the reader reports len() = inf
        frames = [frame[..., 0] for frame in reader.iter_data()]
    assert len(frames) == 3
    assert frames[0].shape[:2] == (52, 50)              # canvas: max(52, 46) x max(49, 49) rounded to even
    assert frames[1].max() <= 2                         # the invalid row is black (allowing codec noise)

    volume = Volume.load(volume_file)
    composer = FrameComposer(volume.window, (52, 50))
    for frame, record in zip(frames[::2], [r for r in PlaneReader().read(csv_path) if r.is_valid]):
        expected = composer.compose(NumpyProjector().project(volume.data, record.plane)).astype(int)
        assert np.abs(frame.astype(int) - expected).mean() < 2   # lossy H.264, but the same picture


@pytest.mark.parametrize("make_args, code, message", [
    (lambda d, v, c: [str(v)], 2, "usage"),
    (lambda d, v, c: [str(d / "none.nrrd"), str(c), str(d / "o.mp4")], 1, "file not found"),
    (lambda d, v, c: [str(v), str(d / "none.csv"), str(d / "o.mp4")], 1, "file not found"),
    (lambda d, v, c: [str(c), str(c), str(d / "o.mp4")], 1, "cannot read NRRD"),
    (lambda d, v, c: [str(v), str(c), str(d / "no_dir" / "o.mp4")], 1, "output folder"),
])
def test_demo_errors(tmp_path, volume_file, capsys, make_args, code, message):
    csv_path = tmp_path / "planes.csv"
    csv_path.write_text(PLANES)
    assert Ex0.main(make_args(tmp_path, volume_file, csv_path)) == code
    assert message in capsys.readouterr().err


def test_demo_fails_when_no_plane_is_valid(tmp_path, volume_file, capsys):
    csv_path = tmp_path / "planes.csv"
    csv_path.write_text("3,0,0,0,1,1,1,2,2,2\n")
    assert Ex0.main([str(volume_file), str(csv_path), str(tmp_path / "o.mp4")]) == 1
    assert "no valid planes" in capsys.readouterr().err
