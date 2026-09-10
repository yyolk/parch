import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_ICONS,
    CLONE_P_PAD,
    CLONE_P_SIZE,
    CLONE_SPINE_W,
    CLONE_STATUS_LABELS,
    CLONE_STRIP_H,
    MUTED,
    PROJECT_COL_WEIGHTS,
    PROJECT_P,
    PROJECT_STATUS_H,
    PROJECT_STATUS_MARK,
    TICK,
    clone_task_count,
    paint_header,
    paint_nav,
    paint_projects,
    paint_projects_clone_faithful,
    paint_toolbar,
    project_card_columns,
    project_card_left_seats,
    project_card_seats,
    projects_clone_a_card,
    projects_clone_a_seats,
    projects_clone_a_well,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_projects_page_after_annual():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert pages[1].dest == "year-2026"
    page = pages[2]
    assert page.dest == "projects-2026"
    assert page.kind == "projects"
    assert page.title == "Projects"
    assert pages[3].dest == "quarter-2026-Q1"

    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    assert board.year == 2026
    assert board.cards == 3
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


def test_project_card_tracks():
    well = Rect(4, 20, 110, 90)
    cards = project_card_seats(well, 3)
    assert len(cards) == 3
    assert cards[0].y == pytest.approx(well.y)
    assert cards[0].x == pytest.approx(well.x)
    assert cards[0].w == pytest.approx(well.w)
    assert cards[-1].bottom == pytest.approx(well.bottom)
    assert cards[1].y > cards[0].bottom
    assert cards[2].y > cards[1].bottom

    left, right = project_card_columns(cards[0])
    assert left.x > cards[0].x
    assert right.right < cards[0].right
    assert left.right < right.x
    assert right.w > left.w
    share = left.w + right.w
    assert left.w / share == pytest.approx(PROJECT_COL_WEIGHTS[0] / sum(PROJECT_COL_WEIGHTS))

    header, tasks, status = project_card_left_seats(left)
    assert header.y == pytest.approx(left.y)
    assert header.x == pytest.approx(left.x)
    assert tasks.y > header.bottom
    assert status.y > tasks.bottom
    assert status.bottom == pytest.approx(left.bottom)
    assert status.h == pytest.approx(PROJECT_STATUS_H)


def test_projects_paint_cards_ticks_and_status():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert texts.count("Todo") == 3
    assert texts.count("Doing") == 3
    assert texts.count("Done") == 3
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 4

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 9

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 3

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_projects_knobs_from_spec():
    spec = Spec(notes_pages=1, project_cards=2, project_tasks=5)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    assert board.cards == 2
    assert board.tasks == 5
    plotter = RecordingPlotter()
    paint_projects(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 2 * 5
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 2


def test_projects_clone_a_tracks():
    well = Rect(4, 20, 110, 90)
    cards, rails = projects_clone_a_seats(well, 3)
    board, rail = projects_clone_a_well(well)
    assert len(cards) == len(rails) == 3
    assert cards[0].x == pytest.approx(board.x)
    assert cards[0].w == pytest.approx(board.w)
    assert cards[-1].bottom == pytest.approx(board.bottom)
    assert rails[0].x == pytest.approx(rail.x)
    assert rails[0].right == pytest.approx(rail.right)
    assert rails[-1].bottom == pytest.approx(rail.bottom)
    assert rail.x > board.right
    assert rail.right == pytest.approx(well.right)
    assert cards[0].y == pytest.approx(rails[0].y)
    assert cards[-1].bottom == pytest.approx(rails[-1].bottom)

    spine, name_h, name_field, tasks, notes, strip = projects_clone_a_card(cards[0])
    assert spine.x == pytest.approx(cards[0].x)
    assert spine.w == pytest.approx(CLONE_SPINE_W)
    assert spine.h == pytest.approx(cards[0].h)
    assert name_h.x > spine.right
    assert name_field.x > name_h.x
    assert name_field.right == pytest.approx(name_h.right)
    assert name_field.h == pytest.approx(PROJECT_P)
    assert tasks.x == pytest.approx(name_h.x)
    assert tasks.y > name_h.bottom
    assert notes.x > name_h.right
    assert notes.y == pytest.approx(name_h.y)
    assert notes.h > name_h.h + tasks.h
    assert strip.y > tasks.bottom
    assert strip.x == pytest.approx(tasks.x)
    assert strip.w == pytest.approx(tasks.w)
    assert strip.h == pytest.approx(CLONE_STRIP_H)
    assert notes.bottom == pytest.approx(strip.bottom)
    assert notes.right < cards[0].right
    assert CLONE_ICONS == (
        "triangle",
        "cross",
        "hexagon",
        "square",
        "crescent",
        "diamond",
        "circle",
        "plus",
        "star",
    )


def test_projects_clone_faithful_paint():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_clone_faithful(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert texts.count("Todo") == 3
    assert texts.count("In Progress") == 3
    assert texts.count("Done") == 3
    assert "#" not in texts
    assert "Doing" not in texts
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts

    p_texts = [op for op in plotter.ops if op[0] == "text" and op[2] == "P"]
    assert all(op[7] == pytest.approx(MUTED) for op in p_texts)
    assert all(op[3] == pytest.approx(CLONE_P_SIZE) for op in p_texts)
    assert all(op[6] == "sans" for op in p_texts)
    assert all(op[8] is True for op in p_texts)
    p_boxes = [
        op[1]
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 3
    for mark, text in zip(p_boxes, p_texts, strict=True):
        label = text[1]
        assert label.x >= mark.x + CLONE_P_PAD - 0.01
        assert label.y >= mark.y + CLONE_P_PAD - 0.01
        assert label.right <= mark.x + mark.w * 0.55
        assert label.bottom <= mark.y + mark.h * 0.5

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    _, _, _, tasks, _, _ = projects_clone_a_card(projects_clone_a_seats(well, 3)[0][0])
    assert len(ticks) == 3 * clone_task_count(tasks)
    assert clone_task_count(tasks) > 4

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 9

    spines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and op[1].w == pytest.approx(CLONE_SPINE_W)
    ]
    assert len(spines) == 3

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3] and not op[2]]
    assert len(fills) > 4  # rail + spines + filled icon scanlines
    dots = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(CLONE_DOT)
        and op[1].h == pytest.approx(CLONE_DOT)
    ]
    assert len(dots) > 30
    assert CLONE_STATUS_LABELS == ("Todo", "In Progress", "Done")


def test_projects_clone_faithful_chrome():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    plotter = RecordingPlotter()
    plotter.begin_page()
    paint_toolbar(plotter, NOMAD)
    paint_header(plotter, NOMAD, page.title, "2026")
    paint_nav(plotter, NOMAD, strip_items(page), strip_active(page.kind))
    paint_projects_clone_faithful(plotter, well_rect(NOMAD), board)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    assert "In Progress" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts


def test_projects_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
