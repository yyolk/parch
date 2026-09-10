from parch.devices.nomad import NOMAD
from parch.fonts import font_dir
from parch.plotter.fpdf2 import Fpdf2Plotter


def test_sans_is_inter_serif_is_liberation():
    root = font_dir()
    assert (root / "Inter-Regular.ttf").is_file()
    assert (root / "Inter-Bold.ttf").is_file()
    assert (root / "LiberationSerif-Regular.ttf").is_file()
    assert (root / "LiberationSerif-Bold.ttf").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()
    assert (root / "LICENSE-Inter").is_file()
    assert (root / "LICENSE").is_file()
    Fpdf2Plotter(NOMAD)
