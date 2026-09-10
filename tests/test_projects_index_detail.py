import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsIndexDetail
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    FOCUS_PITCH,
    INDEX_DETAIL_GAP,
    INDEX_DETAIL_WEIGHTS,
    INDEX_STATUS_MARK,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    TICK,
    index_task_band_height,
    paint_projects_index_detail,
    projects_index_detail_seats,
    projects_index_detail_well_seats,
    projects_index_name_and_marks,
    projects_index_row_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_index_detail import INDEX_ROWS, ProjectsIndexDetailSection
from parch.spec import Spec


def test_index_detail_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_index_detail" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsIndexDetail) for item in page.components)


def test_projects_index_detail_page():
    spec = Spec(notes_pages=1)
    page = ProjectsIndexDetailSection(spec).pages()[0]
    assert page.dest == "projects-index-detail-2026"
    assert page.kind == "projects_index_detail"
    assert page.title == "Projects"
    board = next(item for item in page.components if isinstance(item, ProjectsIndexDetail))
    assert board.year == 2026
    assert board.index_rows == 6
    assert board.tasks == 4
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


def test_projects_index_detail_split_ratios():
    well = well_rect(NOMAD)
    index, detail = projects_index_detail_seats(well)
    assert index.x == pytest.approx(well.x)
    assert detail.right == pytest.approx(well.right)
    assert index.y == pytest.approx(well.y)
    assert detail.bottom == pytest.approx(well.bottom)
    gap = detail.y - index.bottom
    assert gap == pytest.approx(INDEX_DETAIL_GAP)
    leftover = well.h - INDEX_DETAIL_GAP
    assert leftover == pytest.approx(index.h + detail.h)
    assert INDEX_DETAIL_WEIGHTS == (1.0, 2.0)
    assert index.h / leftover == pytest.approx(1 / 3)
    assert detail.h / leftover == pytest.approx(2 / 3)
    assert detail.h / index.h == pytest.approx(2)
    # Well fractions after the 2.6 mm gap (Nomad well 129.1 mm):
    # index 32.66% · gap 2.01% · detail 65.32%.
    assert index.h / well.h == pytest.approx(leftover / 3 / well.h)
    assert detail.h / well.h == pytest.approx(2 * leftover / 3 / well.h)
    assert INDEX_DETAIL_GAP / well.h == pytest.approx(2.6 / well.h)


def test_projects_index_rows_and_detail_seats():
    well = well_rect(NOMAD)
    index, detail = projects_index_detail_seats(well)
    head, lines = projects_index_row_seats(index, 6)
    assert len(lines) == 6
    assert head.y < lines[0].y
    assert lines[-1].bottom <= index.bottom
    name, marks = projects_index_name_and_marks(lines[0])
    assert name.x >= index.x
    assert marks.right <= index.right
    assert name.right < marks.x

    five_head, five = projects_index_row_seats(index, 5)
    assert len(five) == 5
    assert five_head.h == pytest.approx(head.h)

    header, tasks, notes = projects_index_detail_well_seats(detail, 4)
    assert header.y > detail.y
    assert tasks.y > header.bottom
    assert notes.y > tasks.bottom
    assert notes.bottom <= detail.bottom
    assert tasks.h == pytest.approx(index_task_band_height(4))
    assert tasks.h < notes.h
    assert index_task_band_height(4) == pytest.approx(0.4 + TICK + 3 * FOCUS_PITCH + 1.0)


def test_projects_index_detail_paint():
    board = ProjectsIndexDetail(year=2026, index_rows=6, tasks=4)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_index_detail(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    assert texts.count("Doing") == 1
    assert texts.count("Done") == 1
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts
    assert "TO DO" not in texts
    assert "IN PROGRESS" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4

    tiny = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(INDEX_STATUS_MARK)
    ]
    assert len(tiny) == 6 * 3
    assert INDEX_STATUS_MARK < PROJECT_STATUS_MARK

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 1

    card_status = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert card_status == []

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert len(outlines) == 2


def test_projects_index_detail_knobs():
    board = ProjectsIndexDetail(year=2026, index_rows=5, tasks=5)
    plotter = RecordingPlotter()
    paint_projects_index_detail(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 5
    tiny = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(INDEX_STATUS_MARK)
    ]
    assert len(tiny) == 5 * 3
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 1


def test_projects_index_detail_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsIndexDetailSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert INDEX_ROWS == 6
