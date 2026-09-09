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
    assert dests == ["cover", "month-2026-01", "2026-01-05"]
    assert plotter.page == 3

    links = plotter.links()
    assert "month-2026-01" in links
    assert "2026-01-05" in links
    assert "cover" in links

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Schedule" in texts
    assert "Notes" in texts
    assert "toolbar 8 mm - not a well" in texts
