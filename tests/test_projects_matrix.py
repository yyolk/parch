import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsMatrix
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    HABIT_WASH,
    MATRIX_CELL_PAD,
    MATRIX_NAME_GAP,
    MATRIX_NAME_W,
    MATRIX_NOTES_GAP,
    MATRIX_WELL_WEIGHTS,
    PROJECT_P,
    TICK,
    paint_projects,
    paint_projects_matrix,
    projects_matrix_grid,
    projects_matrix_score_box,
    projects_matrix_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_matrix import MATRIX_CRITERIA, MATRIX_ROWS, ProjectsMatrixSection
from parch.spec import Spec


def test_matrix_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_matrix" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsMatrix) for item in page.components)
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    assert board.cards == 3
    assert board.tasks == 4


def test_default_projects_paint_unchanged():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    plotter = RecordingPlotter()
    paint_projects(plotter, well_rect(NOMAD), board)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert texts.count("Todo") == 3
    assert texts.count("Doing") == 3
    assert texts.count("Done") == 3
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 4


def test_projects_matrix_page():
    spec = Spec(notes_pages=1)
    page = ProjectsMatrixSection(spec).pages()[0]
    assert page.dest == "projects-matrix-2026"
    assert page.kind == "projects_matrix"
    assert page.title == "Projects"
    board = next(item for item in page.components if isinstance(item, ProjectsMatrix))
    assert board.year == 2026
    assert board.rows == 5
    assert board.criteria == 5
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


def test_projects_matrix_split_ratios():
    well = well_rect(NOMAD)
    matrix, notes = projects_matrix_seats(well)
    assert matrix.x == pytest.approx(well.x)
    assert notes.right == pytest.approx(well.right)
    assert matrix.y == pytest.approx(well.y)
    assert notes.bottom == pytest.approx(well.bottom)
    gap = notes.y - matrix.bottom
    assert gap == pytest.approx(MATRIX_NOTES_GAP)
    leftover = well.h - MATRIX_NOTES_GAP
    assert leftover == pytest.approx(matrix.h + notes.h)
    assert MATRIX_WELL_WEIGHTS == (2.0, 1.0)
    assert matrix.h / leftover == pytest.approx(2 / 3)
    assert notes.h / leftover == pytest.approx(1 / 3)
    assert matrix.h / notes.h == pytest.approx(2)


def test_projects_matrix_grid_seats():
    well = well_rect(NOMAD)
    matrix, _notes = projects_matrix_seats(well)
    name, heads, bands, score_cols = projects_matrix_grid(matrix, 5, 5)
    assert name.w == pytest.approx(MATRIX_NAME_W)
    assert name.x == pytest.approx(matrix.x)
    assert len(heads) == 5
    assert len(bands) == 5
    assert len(score_cols) == 5
    assert heads[0].y == pytest.approx(matrix.y)
    assert bands[0].y > heads[0].bottom
    assert bands[-1].bottom == pytest.approx(matrix.bottom)
    assert score_cols[0].x == pytest.approx(name.right + MATRIX_NAME_GAP)
    assert score_cols[-1].right == pytest.approx(matrix.right)
    cell = Rect(score_cols[0].x, bands[0].y, score_cols[0].w, bands[0].h)
    box = projects_matrix_score_box(cell)
    assert box.w == pytest.approx(min(cell.w, cell.h) - MATRIX_CELL_PAD)
    assert box.h == pytest.approx(box.w)
    assert box.x > cell.x
    assert box.right < cell.right

    four_name, four_heads, four_bands, four_cols = projects_matrix_grid(matrix, 4, 4)
    assert len(four_heads) == 4
    assert len(four_bands) == 4
    assert len(four_cols) == 4
    assert four_name.w == pytest.approx(name.w)


def test_projects_matrix_paint():
    board = ProjectsMatrix(year=2026, rows=5, criteria=5)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_matrix(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 5
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts
    assert "Impact" not in texts
    assert "Effort" not in texts
    assert "TO DO" not in texts
    assert "IN PROGRESS" not in texts

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 5

    matrix, notes = projects_matrix_seats(well)
    _name, _heads, bands, score_cols = projects_matrix_grid(matrix, 5, 5)
    expected = projects_matrix_score_box(
        Rect(score_cols[0].x, bands[0].y, score_cols[0].w, bands[0].h)
    )
    cells = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(expected.w)
        and op[1].h == pytest.approx(expected.h)
    ]
    assert len(cells) == 5 * 5

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []

    washes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and not op[2] and op[5] == pytest.approx(HABIT_WASH)
    ]
    assert len(washes) == 2

    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(notes.w)
    ]
    assert len(outlines) == 1
    assert outlines[0][1].h == pytest.approx(notes.h)


def test_projects_matrix_knobs():
    board = ProjectsMatrix(year=2026, rows=4, criteria=4)
    plotter = RecordingPlotter()
    paint_projects_matrix(plotter, Rect(4, 20, 110, 90), board)
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 4
    matrix, _notes = projects_matrix_seats(Rect(4, 20, 110, 90))
    _name, _heads, bands, score_cols = projects_matrix_grid(matrix, 4, 4)
    expected = projects_matrix_score_box(
        Rect(score_cols[0].x, bands[0].y, score_cols[0].w, bands[0].h)
    )
    cells = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(expected.w)
        and op[1].h == pytest.approx(expected.h)
    ]
    assert len(cells) == 4 * 4
    washes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and not op[2] and op[5] == pytest.approx(HABIT_WASH)
    ]
    assert len(washes) == 2


def test_projects_matrix_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsMatrixSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert MATRIX_ROWS == 5
    assert MATRIX_CRITERIA == 5
