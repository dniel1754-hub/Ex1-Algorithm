"""The class dataset: its plane CSVs (committed) and NRRD volumes (downloaded into data/, optional)."""
import imageio.v2 as imageio
import nrrd
import numpy as np
import pytest

import Ex0
from conftest import ROOT
from projection import PlaneReader, Volume

DATA = ROOT / "data"
EXPECTED_INVALID = {
    "biscuit_cake.csv": [], "croissant.csv": [], "head.csv": [], "onion.csv": [], "swiss_roll.csv": [],
    "lecturer_example.csv": [3],
    "edge_cases.csv": [7, 9, 10, 11, 12, 13, 14, 15, 16],
}


@pytest.mark.parametrize("name", sorted(EXPECTED_INVALID))
def test_dataset_csv_parses(name):
    records = PlaneReader().read(DATA / name)
    assert records
    assert [r.frame for r in records if not r.is_valid] == EXPECTED_INVALID[name]


@pytest.mark.parametrize("name", ["MRHead_1", "biscuit_cake", "croissant", "onion", "swiss_roll"])
def test_dataset_volume_loads(name):
    path = DATA / f"{name}.nrrd"
    if not path.exists():
        pytest.skip(f"{path.name} not downloaded (see README, Dataset)")
    volume = Volume.load(path)
    assert list(volume.shape) == list(nrrd.read_header(str(path))["sizes"])


def dice_volume():
    """The die described in edge_cases.csv, without its pips: 200 x 180 x 160 uint32."""
    volume = np.zeros((200, 180, 160), np.uint32)
    volume[40:160, 30:150, 20:140] = 100000
    return volume


def test_edge_cases_on_dice(tmp_path, capsys):
    nrrd_path, mp4 = tmp_path / "dice.nrrd", tmp_path / "edge_cases.mp4"
    nrrd.write(str(nrrd_path), dice_volume())

    assert Ex0.main([str(nrrd_path), str(DATA / "edge_cases.csv"), str(mp4)]) == 0

    warned = sorted(int(line.split()[2]) for line in capsys.readouterr().err.splitlines() if "warning" in line)
    assert warned == EXPECTED_INVALID["edge_cases.csv"]
    with imageio.get_reader(str(mp4)) as reader:
        lit = [frame[..., 0].max() > 50 for frame in reader.iter_data()]
    assert len(lit) == 16
    black = [i + 1 for i, on in enumerate(lit) if not on]
    assert black == [6] + EXPECTED_INVALID["edge_cases.csv"]   # 6 misses the die; the rest are invalid
