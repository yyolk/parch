import pytest
from parch.components import CoverTitle, MonthGrid, WeekStrip
from parch.devices.nomad import NOMAD
from parch.fonts import (
    DEFAULT_ROOT_BODY,
    DISPLAY_PT,
    FontCatalog,
    JostRamp,
    STEP_RATIO,
    STEP_WEIGHT,
    TypeFamily,
    TypeInk,
    TypeRole,
    TypeStep,
    font_dir,
    jost_catalog,
)
from parch.geom import Rect
from parch.layouts.planner.painters import (
    paint_cover,
    paint_header,
    paint_month_grid,
    paint_nav,
    paint_week,
)
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


def test_jost_ramp_em_ratios_at_nomad_root():
    ramp = JostRamp(root_body=NOMAD.root_body)
    assert ramp.root_body == DEFAULT_ROOT_BODY == 8.5
    assert ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=DISPLAY_PT)
    assert DISPLAY_PT == 42
    assert ramp.ink("title") == TypeInk(
        family="jost", weight="medium", size=8.5 * 1.3
    )
    assert ramp.ink("chrome") == TypeInk(
        family="jost", weight="book", size=8.5 * 0.87
    )
    assert ramp.ink("body") == TypeInk(family="jost", weight="bold", size=8.5)
    assert ramp.ink("brow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("caption").size == pytest.approx(8.5 * 0.75)
    assert ramp.ink("cell").size == pytest.approx(8.5 * 0.62)
    assert ramp.ink("micro").size == pytest.approx(8.5 * 0.51)
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def test_step_tables_are_closed_and_display_is_fixed():
    steps: frozenset[TypeStep] = frozenset(
        ("display", "title", "brow", "body", "chrome", "caption", "cell", "micro")
    )
    assert set(STEP_WEIGHT) == steps
    assert set(STEP_RATIO) == steps - {"display"}
    assert "display" not in STEP_RATIO
    assert STEP_WEIGHT["display"] == "heavy"
    assert STEP_WEIGHT["title"] == "medium"
    assert STEP_WEIGHT["body"] == "bold"
    assert STEP_WEIGHT["chrome"] == "book"


def test_root_body_override_rescales_title_chrome_body_not_display():
    base = JostRamp(root_body=8.5)
    bumped = JostRamp(root_body=12.0)
    scale = 12.0 / 8.5
    assert bumped.ink("title").size == pytest.approx(base.ink("title").size * scale)
    assert bumped.ink("chrome").size == pytest.approx(base.ink("chrome").size * scale)
    assert bumped.ink("body").size == pytest.approx(base.ink("body").size * scale)
    assert bumped.ink("caption").size == pytest.approx(base.ink("caption").size * scale)
    assert bumped.ink("brow").size == pytest.approx(base.ink("brow").size * scale)
    assert bumped.ink("display").size == base.ink("display").size == 42
    assert bumped.ink("title").family == "jost"
    assert bumped.ink("title").weight == "medium"


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


def test_cover_year_uses_display_step():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == pytest.approx(10)
    assert brow[9] == "medium"
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert _family(specs) is None
    assert specs[6] == "sans"


def test_header_and_nav_use_title_and_chrome():
    ramp = JostRamp()
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Year",
        "2026",
        chip="01",
        ramp=ramp,
    )
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == pytest.approx(8.5 * 1.3)
    assert title[9] == "medium"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == pytest.approx(8.5 * 0.87)
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == pytest.approx(8.5 * 0.87)
    assert meta[9] == "book"
    assert _family(meta) == "jost"

    nav = RecordingPlotter()
    paint_nav(nav, NOMAD, (("Year", "year-2026"), ("Mon", "month-2026-01")), "Year", ramp=ramp)
    year_tab = next(op for op in nav.ops if op[0] == "text" and op[2] == "Year")
    assert year_tab[3] == pytest.approx(8.5 * 0.87)
    assert year_tab[9] == "bold"
    mon_tab = next(op for op in nav.ops if op[0] == "text" and op[2] == "Mon")
    assert mon_tab[9] == "book"
    assert _family(year_tab) == "jost"


def test_cover_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            return TypeInk(family="jost", weight="book", size=12)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=ramp)
    assert ramp.roles == ["brow", "display"]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 12
    assert year[9] == "book"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 12
    assert brow[9] == "book"
    assert _family(brow) == "jost"


def test_header_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            if role == "title":
                return TypeInk(family="jost", weight="bold", size=9)
            return TypeInk(family="jost", weight="book", size=6)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Projects",
        "2026",
        chip="01",
        ramp=ramp,
    )
    assert ramp.roles == ["title", "chrome"]
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


def test_month_and_week_honor_root_override_together():
    """Bumped root rescales title / chrome-adjacent caption / body on one page pair."""
    from datetime import date

    from parch.components.month_grid import MonthCell
    from parch.components.week import WeekDay

    week_days = tuple(
        WeekDay(
            day=date(2026, 7, 13 + i),
            weekday_label=("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[i],
            in_month=True,
            dest=None,
        )
        for i in range(7)
    )
    week = WeekStrip(
        iso_year=2026,
        iso_week=29,
        monday=date(2026, 7, 13),
        sunday=date(2026, 7, 19),
        days=week_days,
    )
    empty = tuple(MonthCell(day=None, dest=None) for _ in range(7))
    grid = MonthGrid(
        year=2026,
        month=7,
        month_name="July",
        weekday_labels=("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
        weeks=(
            (
                MonthCell(day=None, dest=None),
                MonthCell(day=None, dest=None),
                MonthCell(day=1, dest=None),
                MonthCell(day=2, dest=None),
                MonthCell(day=3, dest=None),
                MonthCell(day=4, dest=None),
                MonthCell(day=5, dest=None),
            ),
            empty,
            empty,
            empty,
            empty,
            empty,
        ),
        week_dests=("", "", "", "", "", ""),
        quarter_dest="quarter-2026-Q3",
        habits_dest="month-2026-07-habits",
    )

    base = JostRamp(root_body=8.5)
    bumped = JostRamp(root_body=12.0)
    box = Rect(4, 20, 110, 90)

    month_base = RecordingPlotter()
    paint_month_grid(month_base, box, grid, ramp=base)
    month_bumped = RecordingPlotter()
    paint_month_grid(month_bumped, box, grid, ramp=bumped)
    day_base = next(op for op in month_base.ops if op[0] == "text" and op[2] == "1")
    day_bumped = next(op for op in month_bumped.ops if op[0] == "text" and op[2] == "1")
    assert day_base[3] == pytest.approx(8.5)
    assert day_bumped[3] == pytest.approx(12.0)
    assert _family(day_base) == "jost"
    assert day_base[9] == "bold"

    week_base = RecordingPlotter()
    paint_week(week_base, box, week, ramp=base)
    week_bumped = RecordingPlotter()
    paint_week(week_bumped, box, week, ramp=bumped)
    num_base = next(op for op in week_base.ops if op[0] == "text" and op[2] == "13")
    num_bumped = next(op for op in week_bumped.ops if op[0] == "text" and op[2] == "13")
    assert num_base[3] == pytest.approx(8.5 * 1.3)
    assert num_bumped[3] == pytest.approx(12.0 * 1.3)
    dow = next(op for op in week_base.ops if op[0] == "text" and op[2] == "Mon")
    assert dow[3] == pytest.approx(8.5 * 0.75)


def test_header_root_override_rescales_title_and_chrome():
    base = RecordingPlotter()
    paint_header(base, NOMAD, "Year", "2026", ramp=JostRamp(root_body=8.5))
    bumped = RecordingPlotter()
    paint_header(bumped, NOMAD, "Year", "2026", ramp=JostRamp(root_body=12.0))
    title_base = next(op for op in base.ops if op[0] == "text" and op[2] == "Year")
    title_bumped = next(op for op in bumped.ops if op[0] == "text" and op[2] == "Year")
    meta_base = next(op for op in base.ops if op[0] == "text" and op[2] == "2026")
    meta_bumped = next(op for op in bumped.ops if op[0] == "text" and op[2] == "2026")
    assert title_bumped[3] == pytest.approx(title_base[3] * 12 / 8.5)
    assert meta_bumped[3] == pytest.approx(meta_base[3] * 12 / 8.5)


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.TypeStep is TypeStep
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
    assert fonts.DEFAULT_ROOT_BODY == 8.5
    assert fonts.DISPLAY_PT == 42
