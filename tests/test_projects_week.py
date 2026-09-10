import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsWeek
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    FOCUS_PITCH,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    TICK,
    WEEK_CARD_COL_GAP,
    WEEK_GAP,
    WEEK_HEAD_H,
    WEEK_STATUS_MARK,
    WEEK_TOUCH_W,
    paint_projects_week,
    projects_week_card_seats,
    projects_week_cards,
    projects_week_head_seats,
    projects_week_seats,
    strip_active,
    strip_items,
    week_card_content_height,
    week_task_band_height,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_week import WEEK_CARDS, ProjectsWeekSection
from parch.spec import Spec


def test_projects_week_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_week" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsWeek) for item in page.components)


def test_projects_week_page():
    spec = Spec(notes_pages=1)
    page = ProjectsWeekSection(spec).pages()[0]
    assert page.dest == "projects-week-2026"
    assert page.kind == "projects_week"
    assert page.title == "Projects"
    board = next(item for item in page.components if isinstance(item, ProjectsWeek))
    assert board.year == 2026
    assert board.cards == 2
    assert board.tasks == 4
    assert WEEK_CARDS == 2
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


def test_projects_week_seats_side_by_side():
    well = well_rect(NOMAD)
    head, cards, notes = projects_week_seats(well, 4)
    assert head.y == pytest.approx(well.y)
    assert head.h == pytest.approx(WEEK_HEAD_H)
    assert head.x == pytest.approx(well.x)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.right == pytest.approx(well.right)
    assert cards.y == pytest.approx(head.bottom + WEEK_GAP)
    assert notes.y == pytest.approx(cards.bottom + WEEK_GAP)
    assert cards.h == pytest.approx(week_card_content_height(4))
    assert notes.h > cards.h
    assert week_task_band_height(4) == pytest.approx(0.4 + TICK + 3 * FOCUS_PITCH)

    pair = projects_week_cards(cards, 2)
    assert len(pair) == 2
    assert pair[0].x == pytest.approx(cards.x)
    assert pair[1].right == pytest.approx(cards.right)
    assert pair[0].y == pytest.approx(pair[1].y)
    assert pair[1].x == pytest.approx(pair[0].right + WEEK_CARD_COL_GAP)
    assert pair[0].w == pytest.approx(pair[1].w)

    header, tasks, status = projects_week_card_seats(pair[0], 4)
    assert header.y > pair[0].y
    assert tasks.y > header.bottom
    assert status.y > tasks.bottom
    assert status.bottom < pair[0].bottom
    assert tasks.h == pytest.approx(week_task_band_height(4))

    tag, write, cluster = projects_week_head_seats(head)
    assert tag.x == pytest.approx(head.x)
    assert write.x > tag.right
    assert cluster.right == pytest.approx(head.right)
    assert cluster.w == pytest.approx(WEEK_TOUCH_W)
    assert write.right < cluster.x


def test_projects_week_paint_cards_ticks_and_notes():
    board = ProjectsWeek(year=2026, cards=2, tasks=4)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_week(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 2
    assert texts.count("Todo") == 2
    assert texts.count("Doing") == 2
    assert texts.count("Done") == 2
    assert texts.count("Week") == 1
    assert texts.count("Notes") == 1
    for rejected in ("PROJECT", "Focus", "TO DO", "IN PROGRESS", "DONE!"):
        assert rejected not in texts
    for letter in ("M", "T", "W", "F", "S"):
        assert letter in texts
    assert texts.count("T") == 2
    assert texts.count("S") == 2

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 2 * 4 + 7

    tiny = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(WEEK_STATUS_MARK)
    ]
    assert len(tiny) == 6
    assert WEEK_STATUS_MARK < PROJECT_STATUS_MARK

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 2

    default_status = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert default_status == []

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    # two side-by-side cards are narrower; notes well is full width
    assert len(outlines) == 1


def test_projects_week_knobs():
    board = ProjectsWeek(year=2026, cards=2, tasks=3)
    plotter = RecordingPlotter()
    paint_projects_week(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 2 * 3 + 7
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 2


def test_projects_week_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsWeekSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
