from parch.books import YearPlanner
from parch.calendar import month_days, month_touching_weeks
from parch.components import AnnualGrid, CoverTitle, MonthGrid, Notes, Schedule, WeekStrip
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def _january_dests(*, notes_pages: int) -> list[str]:
    spec = Spec()
    dests = ["cover", spec.year_dest, "month-2026-01"]
    for week in month_touching_weeks(2026, 1, weekday_start=0):
        dests.append(spec.dest_for_week(week[0]))
        for day in week:
            if day.month != 1:
                continue
            dests.append(day.isoformat())
            if notes_pages:
                dests.append(f"{day.isoformat()}-notes-1")
    return dests


def test_components_do_not_draw():
    for cls in (AnnualGrid, CoverTitle, MonthGrid, Notes, Schedule, WeekStrip):
        assert "draw" not in cls.__dict__


def test_book_records_january_dests_and_links():
    spec = Spec(notes_pages=1)
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)

    dests = plotter.dests()
    days = month_days(2026, 1)
    assert dests == _january_dests(notes_pages=1)

    links = plotter.links()
    assert "year-2026" in links
    assert "month-2026-01" in links
    assert "week-2026-W01" in links
    for day in days:
        assert day.isoformat() in links
    assert "2026-01-05-notes-1" in links

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Schedule" in texts
    assert "Notes" in texts
    assert "Notes 1/1" in texts
    assert "Year Book" in texts
    assert "Week 01" in texts
    assert "toolbar 8 mm - not a well" not in texts


def test_notes_pages_zero_skips_wells():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=0), plotter)
    dests = plotter.dests()
    assert dests == _january_dests(notes_pages=0)
    assert not any("-notes-" in name for name in dests)
    assert "2026-01-05-notes-1" not in plotter.links()
