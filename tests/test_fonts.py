from pathlib import Path

from parch.devices import NOMAD
from parch.fonts import font_dir
from parch.plotter.fpdf2 import Fpdf2Plotter


def test_sans_is_barlow_serif_is_liberation():
    root = font_dir()
    assert (root / "Barlow-Regular.ttf").is_file()
    assert (root / "Barlow-Bold.ttf").is_file()
    assert (root / "LICENSE-Barlow").is_file()
    assert (root / "LiberationSerif-Regular.ttf").is_file()
    assert (root / "LiberationSerif-Bold.ttf").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()


def test_plotter_registers_barlow_sans(tmp_path: Path):
    plotter = Fpdf2Plotter(NOMAD)
    families = {name.lower() for name in plotter.pdf.fonts}
    assert "sans" in families
    assert "serif" in families
    assert "sansb" in families
    assert "serifb" in families
    plotter.begin_page()
    plotter.finish(tmp_path / "fonts.pdf")
    assert (tmp_path / "fonts.pdf").is_file()
