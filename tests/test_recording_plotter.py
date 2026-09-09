from parch.books import YearPlanner
from parch.components import CoverTitle, MonthGrid, Notes, Schedule
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_components_do_not_draw():
    for cls in (CoverTitle, MonthGrid, Notes, Schedule):
        assert "draw" not in cls.__dict__


def test_book_records_dests_and_links():
    spec = Spec()
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)

    dests = plotter.dests()
    assert dests == [
        "cover",
        "month-2026-01",
        "2026-01-05",
        "2026-01-05-notes-1",
        "2026-01-05-notes-2",
    ]
    assert plotter.page == 5

    links = plotter.links()
    assert "month-2026-01" in links
    assert "2026-01-05" in links
    assert "2026-01-05-notes-1" in links
    assert "cover" in links

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Schedule" in texts
    assert "Notes" in texts
    assert "Notes 1/2" in texts
    assert "Notes 2/2" in texts
    assert "Year Book" in texts
    assert "toolbar 8 mm - not a well" not in texts


def test_notes_pages_zero_skips_wells():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=0), plotter)
    assert plotter.dests() == ["cover", "month-2026-01", "2026-01-05"]
    assert "2026-01-05-notes-1" not in plotter.links()
