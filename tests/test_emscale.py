"""Em-relative TypeStep ladder: root × ratios, fixed display, restored pre-snap sizes."""

from pathlib import Path

import pytest

from parch.books import YearPlanner
from parch.components import HabitGrid, MonthGrid, ReviewWeekPage
from parch.devices import NOMAD
from parch.fonts import (
    DISPLAY_SIZE,
    JOST_RATIOS,
    ROOT_BODY,
    TYPE_STEPS,
    EffectiveRamp,
    JostRamp,
    TypeInk,
    TypeOverlay,
    TypePatch,
    TypeRef,
    bind_ramp,
    compose_overlays,
    validate_overlay,
)
from parch.layouts.planner.painters import (
    paint_habit_grid,
    paint_habit_grid_rows,
    paint_habit_grid_weekday_zebra,
    paint_header,
    paint_month_grid,
    paint_nav,
    paint_review,
    well_rect,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _one(page, typ):
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} missing {typ.__name__}")


def test_ratios_at_nomad_root_land_on_presnap_cuts():
    ramp = JostRamp(root_body=ROOT_BODY)
    assert ramp.ink("display").size == DISPLAY_SIZE == 42
    assert ramp.ink("title").size == pytest.approx(11)
    assert ramp.ink("eyebrow").size == pytest.approx(10)
    assert ramp.ink("body").size == pytest.approx(8.5)
    assert ramp.ink("chrome").size == pytest.approx(7.4)
    assert ramp.ink("label").size == pytest.approx(6.4)
    assert ramp.ink("caption").size == pytest.approx(5.4)
    assert ramp.ink("micro").size == pytest.approx(4.3)
    assert JOST_RATIOS["body"] == pytest.approx(1.0)
    assert JOST_RATIOS["title"] == pytest.approx(11 / 8.5)
    assert JOST_RATIOS["micro"] == pytest.approx(4.3 / 8.5)
    assert "display" not in JOST_RATIOS


def test_root_bump_rescales_ratio_steps_display_stays_42():
    base = JostRamp(root_body=8.5)
    bumped = JostRamp(root_body=12.0)
    factor = 12.0 / 8.5
    for step in TYPE_STEPS:
        if step == "display":
            assert base.ink(step).size == 42
            assert bumped.ink(step).size == 42
            continue
        assert bumped.ink(step).size == pytest.approx(base.ink(step).size * factor)
        assert bumped.ink(step).weight == base.ink(step).weight
    assert bumped.ink("body").size == pytest.approx(12.0)
    assert bumped.ink("title").size == pytest.approx(12.0 * 11 / 8.5)
    assert bumped.ink("micro").size == pytest.approx(12.0 * 4.3 / 8.5)
    with pytest.raises(ValueError, match="root_body"):
        JostRamp(root_body=0)


def test_overlay_size_is_absolute_override_not_root():
    """Overlay size patches that step only; siblings keep em-derived sizes."""
    over = EffectiveRamp(
        overlay=TypeOverlay(chrome=TypePatch(size=9.0)),
        root_body=12.0,
    )
    bumped = JostRamp(root_body=12.0)
    assert over.ink("chrome") == TypeInk(family="jost", weight="book", size=9.0)
    assert over.ink("chrome", "strong") == TypeInk(family="jost", weight="bold", size=9.0)
    assert over.ink("body").size == pytest.approx(12.0)
    assert over.ink("title").size == pytest.approx(bumped.ink("title").size)
    assert over.ink("micro").size == pytest.approx(bumped.ink("micro").size)
    assert over.ink("display").size == 42
    identity = EffectiveRamp(root_body=12.0)
    assert identity.ink("chrome").size == pytest.approx(bumped.ink("chrome").size)


def test_overlay_still_validates_with_micro():
    from parch.fonts import OverlayOk, jost_defaults

    table = jost_defaults()
    assert "micro" in table
    ok = validate_overlay(
        {"schema_version": 1, "micro": {"size": 3.8, "weight": "book"}},
        table,
    )
    assert isinstance(ok, OverlayOk)
    assert ok.overlay.micro == TypePatch(size=3.8, weight="book")
    ramp = EffectiveRamp(overlay=ok.overlay)
    assert ramp.ink("micro") == TypeInk(family="jost", weight="book", size=3.8)
    assert ramp.ink("body").size == pytest.approx(8.5)


def test_header_and_month_honor_bumped_root():
    bumped = JostRamp(root_body=12.0)
    header = RecordingPlotter(ramp=bumped)
    paint_header(header, NOMAD, "Year", "2026", chip="01", ramp=bumped)
    title = next(op for op in header.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == pytest.approx(12.0 * 11 / 8.5)
    chip = next(op for op in header.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == pytest.approx(12.0 * 7.4 / 8.5)
    year = next(op for op in header.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == pytest.approx(12.0 * 7.4 / 8.5)

    month_page = next(p for p in YearPlanner().pages(Spec(months=(1,), notes_pages=0)) if p.kind == "month")
    ink = RecordingPlotter(ramp=bumped)
    paint_month_grid(ink, well_rect(NOMAD), _one(month_page, MonthGrid), ramp=bumped)
    day = next(op for op in ink.ops if op[0] == "text" and op[2] == "15")
    assert day[3] == pytest.approx(12.0)


def test_restored_presnap_sizes_via_recording_plotter():
    spec = Spec(months=(1,), notes_pages=0, project_index_pages=1)
    pages = YearPlanner().pages(spec)
    well = well_rect(NOMAD)
    ramp = JostRamp()

    nav = RecordingPlotter(ramp=ramp)
    paint_nav(nav, NOMAD, (("Year", "year-2026"), ("Mon", "month-2026-01")), "Year", ramp=ramp)
    nav_sizes = {op[3] for op in nav.ops if op[0] == "text"}
    assert nav_sizes == {7.6}

    month = next(p for p in pages if p.kind == "month")
    month_ink = RecordingPlotter(ramp=ramp)
    paint_month_grid(month_ink, well, _one(month, MonthGrid), ramp=ramp)
    day = next(op for op in month_ink.ops if op[0] == "text" and op[2] == "15")
    assert day[3] == pytest.approx(8.5)
    week_chip = next(
        op for op in month_ink.ops if op[0] == "text" and str(op[2]).startswith("W") and str(op[2])[1:].isdigit()
    )
    assert week_chip[3] == pytest.approx(5.8)

    habit = next(p for p in pages if p.kind == "habits")
    grid = _one(habit, HabitGrid)
    transposed = RecordingPlotter(ramp=ramp)
    paint_habit_grid(transposed, well, grid, ramp=ramp)
    day_one = next(op for op in transposed.ops if op[0] == "text" and op[2] == "1")
    assert day_one[3] == pytest.approx(4.4)
    dow = next(op for op in transposed.ops if op[0] == "text" and op[2] == "T")
    assert dow[3] == pytest.approx(4.4)

    rows_ink = RecordingPlotter(ramp=ramp)
    paint_habit_grid_rows(rows_ink, well, grid, ramp=ramp)
    habit_label = next(op for op in rows_ink.ops if op[0] == "text" and op[2] == "Habit")
    assert habit_label[3] == pytest.approx(5.8)
    rows_day = next(op for op in rows_ink.ops if op[0] == "text" and op[2] == "1")
    assert rows_day[3] == pytest.approx(3.8)

    zebra = RecordingPlotter(ramp=ramp)
    paint_habit_grid_weekday_zebra(zebra, well, grid, ramp=ramp)
    zebra_day = next(op for op in zebra.ops if op[0] == "text" and op[2] == "1")
    assert zebra_day[3] == pytest.approx(3.5)
    zebra_dow = next(op for op in zebra.ops if op[0] == "text" and op[2] == "T")
    assert zebra_dow[3] == pytest.approx(3.3)

    review = next(p for p in pages if p.kind == "review")
    review_ink = RecordingPlotter(ramp=ramp)
    paint_review(review_ink, well, _one(review, ReviewWeekPage), ramp=ramp)
    weekday = next(
        op
        for op in review_ink.ops
        if op[0] == "text" and op[2] in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
    )
    assert weekday[3] == pytest.approx(5.6)
    review_day = next(op for op in review_ink.ops if op[0] == "text" and op[2] == "1")
    assert review_day[3] == pytest.approx(9.2)


def test_mini_month_and_clone_caption_cues(tmp_path: Path):
    spec = Spec(months=(1,), notes_pages=0, project_index_pages=1)
    plotter = RecordingPlotter()
    press(spec, tmp_path / "cues.pdf", plotter=plotter)
    # Mini-month dow letters on the annual grid (micro 4.3); day nums 5.3.
    annual_dow = next(
        op
        for op in plotter.ops
        if op[0] == "text" and op[2] in {"M", "T", "W", "F", "S"} and op[3] == pytest.approx(4.3)
    )
    assert annual_dow[9] == "book"
    mini_day = next(op for op in plotter.ops if op[0] == "text" and op[2] == "15" and op[3] == pytest.approx(5.3))
    assert mini_day[9] in {"book", "bold"}
    clone_p = next(op for op in plotter.ops if op[0] == "text" and op[2] == "P")
    assert clone_p[3] == pytest.approx(5.2)
    date_cue = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Date")
    assert date_cue[3] == pytest.approx(5.8)
    nav = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year" and op[3] == pytest.approx(7.6))
    assert nav[9] in {"book", "bold"}


def test_press_mvp_toml_identity_and_overlay_compose(tmp_path: Path):
    spec = Spec.from_path(Path("examples/mvp.toml"))
    plotter = RecordingPlotter()
    press(
        Spec(year=spec.year, months=(1,), notes_pages=0, project_index_pages=1),
        tmp_path / "mvp-id.pdf",
        plotter=plotter,
    )
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026" and op[3] == 42)
    assert year[9] == "heavy"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    bound = bind_ramp(overlay=compose_overlays(NOMAD.type_overlay, spec.type_overlay), root_body=NOMAD.root_body)
    assert bound.ink("body").size == pytest.approx(8.5)
    assert bound.ink("micro").size == pytest.approx(4.3)
    assert bound.ink("display").size == 42


def test_typeref_size_wins_over_em_and_overlay():
    over = EffectiveRamp(overlay=TypeOverlay(chrome=TypePatch(size=9.1)), root_body=12.0)
    assert over.resolve(TypeRef(step="chrome", size=7.6)) == TypeInk(
        family="jost", weight="book", size=7.6
    )
    assert over.resolve(TypeRef(step="micro")) == over.ink("micro")
    assert over.resolve(TypeRef(step="display")).size == 42
    assert over.ink("micro").size == pytest.approx(12.0 * 4.3 / 8.5)
