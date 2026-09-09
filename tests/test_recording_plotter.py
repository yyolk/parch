from parch.books import YearPlanner
from parch.calendar import month_days
from parch.components import CoverTitle, MonthGrid, Notes, Schedule
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_components_do_not_draw():
    for cls in (CoverTitle, MonthGrid, Notes, Schedule):
        assert "draw" not in cls.__dict__


def test_book_records_january_dests_and_links():
    spec = Spec(notes_pages=1)
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)

    dests = plotter.dests()
    days = month_days(2026, 1)
    assert dests[0] == "cover"
    assert dests[1] == "month-2026-01"
    expected_tail: list[str] = []
    for day in days:
        expected_tail.append(day.isoformat())
        expected_tail.append(f"{day.isoformat()}-notes-1")
    assert dests[2:] == expected_tail

    links = plotter.links()
    assert "cover" in links
    assert "month-2026-01" in links
    for day in days:
        assert day.isoformat() in links
    assert "2026-01-05-notes-1" in links

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Schedule" in texts
    assert "Notes" in texts
    assert "Notes 1/1" in texts
    assert "Year Book" in texts
    assert "toolbar 8 mm - not a well" not in texts


def test_notes_pages_zero_skips_wells():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=0), plotter)
    dests = plotter.dests()
    assert dests[0:2] == ["cover", "month-2026-01"]
    assert dests[2:] == [day.isoformat() for day in month_days(2026, 1)]
    assert not any("-notes-" in name for name in dests)
    assert "2026-01-05-notes-1" not in plotter.links()
