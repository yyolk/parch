from parch.devices import get_device
from parch.fonts import font_dir
from parch.geom import Rect
from parch.plotter.fpdf2 import Fpdf2Plotter


def test_urbanist_sans_and_liberation_serif_are_vendored():
    root = font_dir()
    assert (root / "Urbanist-Regular.ttf").is_file()
    assert (root / "Urbanist-Bold.ttf").is_file()
    assert (root / "LiberationSerif-Regular.ttf").is_file()
    assert (root / "LiberationSerif-Bold.ttf").is_file()
    assert (root / "OFL-Urbanist.txt").is_file()
    assert (root / "AUTHORS-Urbanist.txt").is_file()
    assert (root / "LICENSE").is_file()
    assert (root / "AUTHORS").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()
    assert not (root / "LiberationSans-Bold.ttf").exists()


def test_fpdf2_plotter_loads_urbanist_sans(tmp_path):
    plotter = Fpdf2Plotter(get_device("supernote-nomad"))
    plotter.begin_page()
    plotter.text(Rect(10, 20, 90, 8), "Urbanist Regular")
    plotter.text(Rect(10, 30, 90, 8), "Urbanist Bold", bold=True)
    plotter.text(Rect(10, 40, 90, 8), "Liberation Serif", face="serif", bold=True)
    out = tmp_path / "faces.pdf"
    plotter.finish(out)
    assert out.is_file() and out.stat().st_size > 0
