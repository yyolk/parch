import inspect

from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import JostRamp, TypeInk, TypeRole, font_dir
from parch.layouts.planner.painters import paint_cover, paint_header
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight


def test_jost_weight_files_and_defaults():
    root = font_dir()
    assert (root / "Jost-400-Book.ttf").is_file()
    assert (root / "Jost-500-Medium.ttf").is_file()
    assert (root / "Jost-700-Bold.ttf").is_file()
    assert (root / "Jost-800-Heavy.ttf").is_file()
    assert (root / "LICENSE").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()
    assert not (root / "LiberationSerif-Regular.ttf").exists()
    assert resolve_weight("sans", False, None) == "book"
    assert resolve_weight("sans", True, None) == "bold"
    assert resolve_weight("serif", False, None) == "medium"
    assert resolve_weight("serif", True, None) == "medium"
    assert resolve_weight("serif", True, "heavy") == "heavy"
    Fpdf2Plotter(NOMAD)


def test_jost_ramp_role_map():
    ramp = JostRamp()
    assert ramp.ink("cover_year") == TypeInk(face="serif", weight="heavy", size=42)
    assert ramp.ink("cover_brow") == TypeInk(face="serif", weight="medium", size=10)
    assert ramp.ink("page_title") == TypeInk(face="serif", weight="medium", size=11)
    assert ramp.ink("chrome") == TypeInk(face="sans", weight="book", size=7.4)


def _cover() -> CoverTitle:
    return CoverTitle(
        year=2026,
        subtitle="",
        device_name="nomad",
        cta_label="",
        cta_dest="year-2026",
    )


def test_cover_year_uses_heavy_via_jost_ramp():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[6] == "serif"
    assert year[9] == "heavy"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[6] == "serif"
    assert brow[9] == "medium"


def test_cover_asks_roles_not_literal_heavy():
    source = inspect.getsource(paint_cover)
    assert 'weight="heavy"' not in source
    assert 'ramp.ink("cover_year")' in source
    assert 'ramp.ink("cover_brow")' in source


def test_cover_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            return TypeInk(face="sans", weight="book", size=12)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=ramp)
    assert ramp.roles == ["cover_brow", "cover_year", "chrome"]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 12
    assert year[6] == "sans"
    assert year[9] == "book"


def test_header_asks_title_and_chrome_roles():
    source = inspect.getsource(paint_header)
    assert 'face="serif"' not in source
    assert 'face="sans"' not in source
    assert 'ramp.ink("page_title")' in source
    assert 'ramp.ink("chrome")' in source


def test_header_honors_stub_ramp():
    class StubRamp:
        def ink(self, role: TypeRole) -> TypeInk:
            if role == "page_title":
                return TypeInk(face="sans", weight="bold", size=9)
            return TypeInk(face="serif", weight="medium", size=6)

    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Projects",
        "2026",
        chip="01",
        ramp=StubRamp(),
    )
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Projects")
    assert title[3] == 9
    assert title[6] == "sans"
    assert title[9] == "bold"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 6
    assert chip[6] == "serif"
    assert chip[9] == "medium"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[6] == "serif"
    assert meta[9] == "medium"
