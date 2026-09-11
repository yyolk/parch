"""Thesis H — component TypoNeeds match what RecordingPlotter saw.

Painters ask ``typography()``, resolve via the ramp, then draw. Role names
live on the companion needs type, not in geometry code.
"""

from parch.books import YearPlanner
from parch.components import (
    AnnualGrid,
    CoverTitle,
    HeaderChrome,
    MonthGrid,
    Notes,
    Priorities,
    ProjectsIndex,
    Schedule,
    WeekStrip,
)
from parch.devices.nomad import NOMAD
from parch.fonts import JostRamp, TypeInk, TypeRole
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner.painters import (
    paint_annual,
    paint_cover,
    paint_header,
    paint_month_grid,
    paint_notes,
    paint_priorities,
    paint_projects_index,
    paint_schedule,
    paint_week,
    well_rect,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec


class RecordingRamp:
    """Records every role the painter asks. Delegates ink to ``JostRamp``."""

    def __init__(self) -> None:
        self.inner: TypeRamp = JostRamp()
        self.roles: list[TypeRole] = []

    def ink(self, role: TypeRole) -> TypeInk:
        self.roles.append(role)
        return self.inner.ink(role)


def _cover() -> CoverTitle:
    return CoverTitle(
        year=2026,
        subtitle="",
        device_name="nomad",
        cta_label="",
        cta_dest="year-2026",
    )


def _pages():
    return YearPlanner().pages(Spec(notes_pages=1))


def _one(pages, dest: str, typ):
    page = next(page for page in pages if page.dest == dest)
    return next(item for item in page.components if isinstance(item, typ))


def _text_ops(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "text"]


def _recorded_ink(op: tuple) -> TypeInk:
    family, weight, size = op[10], op[9], op[3]
    assert family is not None and weight is not None
    return TypeInk(family=family, weight=weight, size=size)


def _assert_needs_match_plotter(needs, ramp: RecordingRamp, plotter: RecordingPlotter) -> None:
    assert set(ramp.roles) == set(needs.roles())
    allowed = {JostRamp().ink(role) for role in needs.roles()}
    for op in _text_ops(plotter):
        assert _recorded_ink(op) in allowed


def test_cover_typo_needs_match_recording():
    cover = _cover()
    needs = cover.typography()
    ramp = RecordingRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, cover, ramp=ramp)
    _assert_needs_match_plotter(needs, ramp, plotter)
    texts = {op[2]: op for op in _text_ops(plotter)}
    assert _recorded_ink(texts["2026"]) == JostRamp().ink(needs.year)
    assert _recorded_ink(texts["Year Book"]) == JostRamp().ink(needs.brow)
    spec = next(op for op in _text_ops(plotter) if "monday weeks" in str(op[2]))
    assert _recorded_ink(spec) == JostRamp().ink(needs.spec)


def test_header_typo_needs_match_recording():
    header = HeaderChrome(title="Year", meta="2026", chip="01")
    needs = header.typography()
    ramp = RecordingRamp()
    plotter = RecordingPlotter()
    paint_header(plotter, NOMAD, header, ramp=ramp)
    _assert_needs_match_plotter(needs, ramp, plotter)
    texts = {op[2]: op for op in _text_ops(plotter)}
    assert _recorded_ink(texts["Year"]) == JostRamp().ink(needs.title)
    assert _recorded_ink(texts["01"]) == JostRamp().ink(needs.chrome)
    assert _recorded_ink(texts["2026"]) == JostRamp().ink(needs.chrome)


def test_year_typo_needs_match_recording():
    grid = _one(_pages(), "year-2026", AnnualGrid)
    needs = grid.typography()
    ramp = RecordingRamp()
    plotter = RecordingPlotter()
    paint_annual(plotter, well_rect(NOMAD), grid, ramp=ramp)
    _assert_needs_match_plotter(needs, ramp, plotter)
    jan = next(op for op in _text_ops(plotter) if op[2] == "Jan")
    assert _recorded_ink(jan) == JostRamp().ink(needs.name_on)
    dow = next(op for op in _text_ops(plotter) if op[2] == "M")
    assert _recorded_ink(dow) == JostRamp().ink(needs.dow)
    day = next(op for op in _text_ops(plotter) if op[2] == "15")
    assert _recorded_ink(day) in {JostRamp().ink(needs.day), JostRamp().ink(needs.day_on)}


def test_month_typo_needs_match_recording():
    grid = _one(_pages(), "month-2026-07", MonthGrid)
    needs = grid.typography()
    ramp = RecordingRamp()
    plotter = RecordingPlotter()
    paint_month_grid(plotter, well_rect(NOMAD), grid, ramp=ramp)
    _assert_needs_match_plotter(needs, ramp, plotter)
    dow = next(op for op in _text_ops(plotter) if op[2] == "M")
    assert _recorded_ink(dow) == JostRamp().ink(needs.dow)
    week = next(op for op in _text_ops(plotter) if str(op[2]).startswith("W") and str(op[2])[1:2].isdigit())
    assert _recorded_ink(week) == JostRamp().ink(needs.week)
    day = next(op for op in _text_ops(plotter) if op[2] == "15")
    assert _recorded_ink(day) == JostRamp().ink(needs.day)


def test_week_typo_needs_match_recording():
    week = _one(_pages(), "week-2026-W01", WeekStrip)
    needs = week.typography()
    ramp = RecordingRamp()
    plotter = RecordingPlotter()
    paint_week(plotter, well_rect(NOMAD), week, ramp=ramp)
    _assert_needs_match_plotter(needs, ramp, plotter)
    dow = next(op for op in _text_ops(plotter) if op[2] == "Mon")
    assert _recorded_ink(dow) == JostRamp().ink(needs.dow)
    day = next(op for op in _text_ops(plotter) if op[2] == "29")
    assert _recorded_ink(day) == JostRamp().ink(needs.day)
    month = next(op for op in _text_ops(plotter) if op[2] == "Dec")
    assert _recorded_ink(month) == JostRamp().ink(needs.month)


def test_daily_well_typo_needs_match_recording():
    pages = _pages()
    page = next(item for item in pages if item.dest == "2026-07-15")
    schedule = next(item for item in page.components if isinstance(item, Schedule))
    notes = next(item for item in page.components if isinstance(item, Notes))
    priorities = next(item for item in page.components if isinstance(item, Priorities))
    box = well_rect(NOMAD)

    sched_ramp = RecordingRamp()
    sched_plot = RecordingPlotter()
    paint_schedule(sched_plot, box, schedule, ramp=sched_ramp)
    _assert_needs_match_plotter(schedule.typography(), sched_ramp, sched_plot)
    label = next(op for op in _text_ops(sched_plot) if op[2] == "Schedule")
    assert _recorded_ink(label) == JostRamp().ink(schedule.typography().label)
    hour = next(op for op in _text_ops(sched_plot) if op[2].strip().isdigit())
    assert _recorded_ink(hour) == JostRamp().ink(schedule.typography().hour)

    notes_ramp = RecordingRamp()
    notes_plot = RecordingPlotter()
    paint_notes(notes_plot, box, notes, ramp=notes_ramp)
    _assert_needs_match_plotter(notes.typography(), notes_ramp, notes_plot)

    prio_ramp = RecordingRamp()
    prio_plot = RecordingPlotter()
    paint_priorities(prio_plot, box, priorities, ramp=prio_ramp)
    _assert_needs_match_plotter(priorities.typography(), prio_ramp, prio_plot)


def test_projects_ticket_typo_needs_match_recording():
    index = _one(_pages(), "projects-index-2026-01", ProjectsIndex)
    needs = index.typography()
    ramp = RecordingRamp()
    plotter = RecordingPlotter()
    paint_projects_index(plotter, well_rect(NOMAD), index, ramp=ramp)
    _assert_needs_match_plotter(needs, ramp, plotter)
    stub = next(op for op in _text_ops(plotter) if op[2] == "01")
    assert _recorded_ink(stub) == JostRamp().ink(needs.stub)


def test_typography_contract_sits_on_the_dataclass():
    cover = _cover()
    assert cover.typography().roles() == ("cover_year", "cover_brow", "cover_spec")
    header = HeaderChrome(title="Year", meta="2026")
    assert header.typography().roles() == ("page_title", "chrome")
    grid = _one(_pages(), "year-2026", AnnualGrid)
    assert grid.months[0].typography().roles() == grid.typography().roles()
