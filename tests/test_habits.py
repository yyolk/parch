import pytest

from parch.books import YearPlanner
from parch.components import HabitGrid
from parch.geom import Rect
from parch.layouts.planner.painters import (
    HABIT_TRANSPOSED_COLS,
    HABIT_WASH,
    HABIT_WASH_CROSS,
    habit_dow_letter,
    habit_seats_transposed,
    paint_habit_grid,
    paint_habit_grid_transposed,
    paint_habit_grid_weekday_zebra,
    strip_active,
    strip_items,
)
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
    fills = [op for op in ink.ops if op[0] == "rect" and op[3]]
    assert fills == []
    labels = [op[2] for op in ink.ops if op[0] == "text"]
    assert "1" in labels and "31" in labels
    assert "Habit" in labels


def test_habit_transposed_seat_and_paint():
    box = Rect(4, 20, 110, 120)
    day_col, names, bands = habit_seats_transposed(box, 31, HABIT_TRANSPOSED_COLS)
    assert len(names) == 10
    assert len(bands) == 31
    assert day_col.x == pytest.approx(box.x)
    assert names[0].y == pytest.approx(box.y)
    assert bands[0].y > names[0].bottom
    assert bands[-1].bottom == pytest.approx(box.bottom)

    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "month-2026-07-habits")
    grid = next(item for item in page.components if isinstance(item, HabitGrid))
    ink = RecordingPlotter()
    paint_habit_grid_transposed(ink, box, grid)
    cells = [op for op in ink.ops if op[0] == "rect" and op[2] and not op[3]]
    assert len(cells) == 10 * 31
    fills = [op for op in ink.ops if op[0] == "rect" and op[3] and not op[2]]
    grays = {op[5] for op in fills}
    assert grays == {HABIT_WASH, HABIT_WASH_CROSS}
    assert HABIT_WASH_CROSS > 0.9
    odd_rows, odd_cols = 31 // 2, HABIT_TRANSPOSED_COLS // 2
    assert len(fills) == odd_rows + odd_cols + odd_rows * odd_cols
    labels = [op[2] for op in ink.ops if op[0] == "text"]
    assert "1" in labels and "31" in labels
    assert habit_dow_letter(2026, 7, 1) == "W"
    assert habit_dow_letter(2026, 7, 6) == "M"
    assert habit_dow_letter(2026, 7, 31) == "F"
    assert labels.count("W") >= 1
    assert "F" in labels and "M" in labels
    assert all("·" not in label for label in labels)


def test_habit_weekday_zebra_paint():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "month-2026-07-habits")
    grid = next(item for item in page.components if isinstance(item, HabitGrid))
    ink = RecordingPlotter()
    paint_habit_grid_weekday_zebra(ink, Rect(4, 20, 110, 120), grid)
    cells = [op for op in ink.ops if op[0] == "rect" and op[2] and not op[3]]
    assert len(cells) == 12 * 31
    fills = [op for op in ink.ops if op[0] == "rect" and op[3] and not op[2]]
    assert len(fills) == grid.rows // 2
    assert {op[5] for op in fills} == {HABIT_WASH}
    labels = [op[2] for op in ink.ops if op[0] == "text"]
    assert "1" in labels and "31" in labels
    assert "W" in labels and "F" in labels and "M" in labels
    assert "Habit" in labels
    assert all("1W" not in label and "31F" not in label for label in labels)
