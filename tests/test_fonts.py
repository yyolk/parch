from parch.devices.nomad import NOMAD
from parch.fonts import font_dir
from parch.plotter.fpdf2 import Fpdf2Plotter


def test_sans_is_liberation_serif_is_besley():
    root = font_dir()
    assert (root / "LiberationSans-Regular.ttf").is_file()
    assert (root / "LiberationSans-Bold.ttf").is_file()
    assert (root / "Besley-Regular.ttf").is_file()
    assert (root / "Besley-Bold.ttf").is_file()
    assert not (root / "LiberationSerif-Regular.ttf").exists()
    assert not (root / "LiberationSerif-Bold.ttf").exists()
    assert (root / "LICENSE").is_file()
    assert (root / "AUTHORS").is_file()
    assert (root / "LICENSE-Besley").is_file()
    assert (root / "AUTHORS-Besley").is_file()
    Fpdf2Plotter(NOMAD)
