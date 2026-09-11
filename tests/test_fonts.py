import pytest
from parch.components import CoverTitle, MonthGrid
from parch.devices.nomad import NOMAD
from parch.fonts import (
    BodyRole,
    ChromeRole,
    FontCatalog,
    JostBodyRamp,
    JostChromeRamp,
    TypeFamily,
    TypeInk,
    font_dir,
    jost_catalog,
    jost_ramps,
)
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import paint_cover, paint_header, paint_month_grid, paint_nav
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight


def test_jost_weight_files_and_defaults():
    root = font_dir()
    assert (root / "Jost-400-Book.ttf").is_file()
    assert (root / "Jost-500-Medium.ttf").is_file()
    assert (root / "Jost-700-Bold.ttf").is_file()
    assert (root / "Jost-800-Heavy.ttf").is_file()
    assert (root / "LICENSE").is_file()
    assert (root / "AUTHORS").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()
    assert not (root / "LiberationSerif-Regular.ttf").exists()
    assert resolve_weight("sans", False, None) == "book"
    assert resolve_weight("sans", True, None) == "bold"
    assert resolve_weight("serif", False, None) == "medium"
    assert resolve_weight("serif", True, None) == "medium"
    assert resolve_weight("serif", True, "heavy") == "heavy"
    Fpdf2Plotter(NOMAD)


def test_jost_catalog_is_four_cuts():
    catalog = jost_catalog()
    assert set(catalog.cuts) == {
        ("jost", "book"),
        ("jost", "medium"),
        ("jost", "bold"),
        ("jost", "heavy"),
    }
    assert catalog.register_name("jost", "heavy") == "jost:heavy"
    with pytest.raises(KeyError, match="family='jost' weight='hairline'"):
        catalog.path("jost", "hairline")


def test_jost_chrome_ramp_role_map():
    chrome = JostChromeRamp()
    assert chrome.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert chrome.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=10)
    assert chrome.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)
    assert chrome.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert chrome.ink("nav") == TypeInk(family="jost", weight="book", size=7.6)
    assert set(chrome.catalog.cuts) == set(jost_catalog().cuts)


def test_jost_body_ramp_role_map():
    body = JostBodyRamp()
    assert body.ink("body") == TypeInk(family="jost", weight="book", size=7.0)
    assert body.ink("label") == TypeInk(family="jost", weight="book", size=6.4)
    assert body.ink("caption") == TypeInk(family="jost", weight="book", size=5.8)
    assert body.ink("calendar_num") == TypeInk(family="jost", weight="bold", size=8.5)
    assert body.ink("strong") == TypeInk(family="jost", weight="bold", size=7.2)
    assert set(body.catalog.cuts) == set(jost_catalog().cuts)


def test_jost_ramps_share_one_catalog():
    chrome, body = jost_ramps()
    assert chrome.catalog is body.catalog
    assert set(chrome.catalog.cuts) == set(jost_catalog().cuts)


def test_layout_holds_explicit_chrome_and_body():
    chrome, body = jost_ramps()
    layout = PlannerLayout(chrome=chrome, body=body)
    assert layout.chrome is chrome
    assert layout.body is body


def test_layout_defaults_share_jost_catalog():
    layout = PlannerLayout()
    assert layout.chrome.catalog is layout.body.catalog
    assert isinstance(layout.chrome, JostChromeRamp)
    assert isinstance(layout.body, JostBodyRamp)


def _cover() -> CoverTitle:
    return CoverTitle(
        year=2026,
        subtitle="",
        device_name="nomad",
        cta_label="",
        cta_dest="year-2026",
    )


def _family(op: tuple[object, ...]) -> object:
    return op[10]


def test_cover_year_uses_jost_heavy_via_chrome_ramp():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), chrome=JostChromeRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[9] == "medium"
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert _family(specs) is None
    assert specs[6] == "sans"


def test_header_chrome_is_jost_book_via_chrome_ramp():
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Year",
        "2026",
        chip="01",
        chrome=JostChromeRamp(),
    )
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 11
    assert title[9] == "medium"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 7.4
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 7.4
    assert meta[9] == "book"
    assert _family(meta) == "jost"


def test_nav_uses_chrome_ramp_nav_role():
    plotter = RecordingPlotter()
    paint_nav(
        plotter,
        NOMAD,
        (("Year", "year-2026"), ("Mon", "month-2026-01")),
        "Year",
        chrome=JostChromeRamp(),
    )
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert year[3] == 7.6
    assert year[9] == "bold"
    assert _family(year) == "jost"
    mon = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Mon")
    assert mon[3] == 7.6
    assert mon[9] == "book"
    assert _family(mon) == "jost"


def test_cover_honors_stub_chrome():
    class StubChrome:
        def __init__(self) -> None:
            self.roles: list[ChromeRole] = []

        def ink(self, role: ChromeRole) -> TypeInk:
            self.roles.append(role)
            return TypeInk(family="jost", weight="book", size=12)

    chrome = StubChrome()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), chrome=chrome)
    assert chrome.roles == ["cover_brow", "cover_year"]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 12
    assert year[9] == "book"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 12
    assert brow[9] == "book"
    assert _family(brow) == "jost"


def test_header_honors_stub_chrome():
    class StubChrome:
        def __init__(self) -> None:
            self.roles: list[ChromeRole] = []

        def ink(self, role: ChromeRole) -> TypeInk:
            self.roles.append(role)
            if role == "page_title":
                return TypeInk(family="jost", weight="bold", size=9)
            return TypeInk(family="jost", weight="book", size=6)

    chrome = StubChrome()
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Projects",
        "2026",
        chip="01",
        chrome=chrome,
    )
    assert chrome.roles == ["page_title", "chrome"]
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Projects")
    assert title[3] == 9
    assert title[9] == "bold"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 6
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 6
    assert meta[9] == "book"
    assert _family(meta) == "jost"


def _january() -> MonthGrid:
    from parch.sections.month import MonthSection
    from parch.spec import Spec

    page = next(p for p in MonthSection(Spec()).pages_for(1) if p.kind == "month")
    return next(item for item in page.components if isinstance(item, MonthGrid))


def test_month_grid_uses_body_ramp_roles():
    plotter = RecordingPlotter()
    paint_month_grid(plotter, Rect(4, 20, 110, 120), _january(), body=JostBodyRamp())
    weekday = next(op for op in plotter.ops if op[0] == "text" and op[2] == "M")
    assert weekday[3] == 5.8
    assert weekday[9] == "book"
    assert _family(weekday) == "jost"
    week = next(op for op in plotter.ops if op[0] == "text" and str(op[2]).startswith("W"))
    assert week[3] == 5.8
    assert week[9] == "book"
    assert _family(week) == "jost"
    day = next(op for op in plotter.ops if op[0] == "text" and op[2] == "1")
    assert day[3] == 8.5
    assert day[9] == "bold"
    assert _family(day) == "jost"


def test_month_grid_honors_stub_body():
    class StubBody:
        def __init__(self) -> None:
            self.roles: list[BodyRole] = []

        def ink(self, role: BodyRole) -> TypeInk:
            self.roles.append(role)
            if role == "calendar_num":
                return TypeInk(family="jost", weight="heavy", size=14)
            return TypeInk(family="jost", weight="medium", size=4)

    body = StubBody()
    plotter = RecordingPlotter()
    paint_month_grid(plotter, Rect(4, 20, 110, 120), _january(), body=body)
    assert set(body.roles) == {"caption", "calendar_num"}
    weekday = next(op for op in plotter.ops if op[0] == "text" and op[2] == "M")
    assert weekday[3] == 4
    assert weekday[9] == "medium"
    assert _family(weekday) == "jost"
    day = next(op for op in plotter.ops if op[0] == "text" and op[2] == "15")
    assert day[3] == 14
    assert day[9] == "heavy"
    assert _family(day) == "jost"


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostChromeRamp is JostChromeRamp
    assert fonts.JostBodyRamp is JostBodyRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.jost_catalog is jost_catalog
    assert fonts.jost_ramps is jost_ramps
    assert fonts.FontCatalog is FontCatalog
