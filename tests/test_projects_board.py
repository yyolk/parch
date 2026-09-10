from pathlib import Path

import pytest
from pypdf import PdfReader

from parch.books import ProjectsColumnsBook, YearPlanner, planner_book
from parch.components import ProjectsColumns
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    BOARD_COL_GAP,
    BOARD_LABELS,
    TICK,
    paint_projects_columns,
    project_board_card_seats,
    project_board_column_seats,
    project_board_columns,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.press import main, press
from parch.spec import Spec


def test_year_book_does_not_grow_a_board_page():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert pages[2].kind == "projects"
    assert pages[2].dest == "projects-2026"
    assert all(page.kind != "projects_board" for page in pages)
    assert all(page.dest != "projects-board-2026" for page in pages)


def test_projects_board_page_and_seven_tabs():
    spec = Spec(notes_pages=1)
    pages = ProjectsColumnsBook().pages(spec)
    assert len(pages) == 1
    page = pages[0]
    assert page.dest == "projects-board-2026"
    assert page.kind == "projects_board"
    assert page.title == "Projects"

    board = next(item for item in page.components if isinstance(item, ProjectsColumns))
    assert board.year == 2026
    assert board.cards == 4
    assert board.ticks == 3

    assert strip_active(page.kind) == ""
    assert strip_items(page) == (
        ("Year", "year-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
    )


def test_project_board_tracks():
    well = Rect(4, 20, 110, 90)
    cols = project_board_columns(well)
    assert len(cols) == 3
    assert cols[0].x == pytest.approx(well.x)
    assert cols[-1].right == pytest.approx(well.right)
    assert cols[1].x > cols[0].right
    assert cols[2].x > cols[1].right
    assert cols[0].w == pytest.approx(cols[1].w)
    assert cols[0].w == pytest.approx((well.w - 2 * BOARD_COL_GAP) / 3)

    header, cards = project_board_column_seats(cols[0], 4)
    assert header.y == pytest.approx(cols[0].y)
    assert header.x == pytest.approx(cols[0].x)
    assert len(cards) == 4
    assert cards[0].y > header.bottom
    assert cards[-1].bottom == pytest.approx(cols[0].bottom)
    assert cards[1].y > cards[0].bottom

    name, ticks = project_board_card_seats(cards[0])
    assert name.x > cards[0].x
    assert name.right < cards[0].right
    assert ticks.y >= name.bottom
    assert ticks.bottom < cards[0].bottom


def test_projects_columns_paint_headers_cards_and_ticks():
    spec = Spec(notes_pages=1)
    page = ProjectsColumnsBook().pages(spec)[0]
    board = next(item for item in page.components if isinstance(item, ProjectsColumns))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_columns(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Todo") == 1
    assert texts.count("Doing") == 1
    assert texts.count("Done") == 1
    assert list(BOARD_LABELS) == ["Todo", "Doing", "Done"]
    assert "P" not in texts
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts
    assert "IN PROGRESS" not in texts
    assert "DONE!" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 4 * 3

    cards = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w > 20
    ]
    assert len(cards) == 12

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_projects_board_knobs_from_spec():
    spec = Spec(notes_pages=1, book="projects_columns", board_cards=3, board_ticks=2)
    page = ProjectsColumnsBook().pages(spec)[0]
    board = next(item for item in page.components if isinstance(item, ProjectsColumns))
    assert board.cards == 3
    assert board.ticks == 2
    plotter = RecordingPlotter()
    paint_projects_columns(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 3 * 2
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Todo") == 1


def test_projects_board_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1, book="projects_columns")
    page = ProjectsColumnsBook().pages(spec)[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert "Todo" in texts
    assert "Doing" in texts
    assert "Done" in texts


def test_planner_book_routes_throwaway_and_year():
    assert isinstance(planner_book(Spec()), YearPlanner)
    assert isinstance(planner_book(Spec(book="projects_columns")), ProjectsColumnsBook)


def test_press_projects_columns_one_page(tmp_path: Path):
    out = tmp_path / "board.pdf"
    press(Spec(notes_pages=1, book="projects_columns"), out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    raw = reader.named_destinations or {}
    dests = {str(key).lstrip("/") for key in raw}
    assert "projects-board-2026" in dests
    assert "projects-2026" not in dests


def test_cli_press_exp_toml(tmp_path: Path):
    out = tmp_path / "exp.pdf"
    assert main(["press", "examples/exp-projects-a.toml", "-o", str(out)]) == 0
    assert out.is_file()
    assert len(PdfReader(out).pages) == 1
