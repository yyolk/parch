from parch.books import YearPlanner
from parch.components import HabitGrid
from parch.geom import Rect
from parch.layouts.planner.painters import paint_habit_grid, strip_active, strip_items
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_habit_pages_follow_each_month():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[6:10] == [
        "month-2026-01",
        "month-2026-01-habits",
        "month-2026-02",
        "month-2026-02-habits",
    ]
    habits = [name for name in dests if name.endswith("-habits")]
    assert habits == [f"month-2026-{month:02d}-habits" for month in range(1, 13)]

    july = next(page for page in pages if page.dest == "month-2026-07-habits")
    assert july.kind == "habits"
    assert july.title == "Habits · July 2026"
    assert strip_active(july.kind) == ""
    assert ("Mon", "month-2026-07") in strip_items(july)
    assert ("Quar", "quarter-2026-Q3") in strip_items(july)
    assert all(label != "Habits" for label, _ in strip_items(july))

    grid = next(item for item in july.components if isinstance(item, HabitGrid))
    assert grid.days == 31
    assert grid.rows == 12
    assert grid.month_dest == "month-2026-07"
    assert grid.day_dests[14] == "2026-07-15"

    feb = next(page for page in pages if page.dest == "month-2026-02-habits")
    feb_grid = next(item for item in feb.components if isinstance(item, HabitGrid))
    assert feb_grid.days == 28


def test_habit_paint_smoke_and_month_chip_link():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=1), plotter)
    dests = plotter.dests()
    links = plotter.links()
    assert "month-2026-07-habits" in dests
    assert "month-2026-07-habits" in links
    assert "month-2026-01-habits" in links
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Habits · July 2026" in texts
    assert "Habits" in texts
    assert "Habit" in texts
    assert "31" in texts

    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "month-2026-01-habits")
    grid = next(item for item in page.components if isinstance(item, HabitGrid))
    ink = RecordingPlotter()
    paint_habit_grid(ink, Rect(4, 20, 110, 120), grid)
    cells = [op for op in ink.ops if op[0] == "rect" and op[2] and not op[3]]
    assert len(cells) == 12 * 31
    labels = [op[2] for op in ink.ops if op[0] == "text"]
    assert "1" in labels and "31" in labels
    assert "Habit" in labels
