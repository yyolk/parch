import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsHorizon
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    HORIZON_GAP,
    HORIZON_INSET_X,
    HORIZON_INSET_Y,
    HORIZON_LABEL_GAP,
    HORIZON_LABEL_H,
    HORIZON_LABELS,
    HORIZON_NOTE_GAP,
    HORIZON_SLOT_GAP,
    HORIZON_SLOT_NAME_H,
    PROJECT_NOTE_PITCH,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    TICK,
    paint_projects_horizon,
    projects_horizon_band_seats,
    projects_horizon_name_and_ticks,
    projects_horizon_seats,
    projects_horizon_slot_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_horizon import HORIZON_SLOTS, HORIZON_TICKS, ProjectsHorizonSection
from parch.spec import Spec


def test_horizon_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_horizon" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsHorizon) for item in page.components)


def test_projects_horizon_page():
    spec = Spec(notes_pages=1)
    page = ProjectsHorizonSection(spec).pages()[0]
    assert page.dest == "projects-horizon-2026"
    assert page.kind == "projects_horizon"
    assert page.title == "Projects"
    board = next(item for item in page.components if isinstance(item, ProjectsHorizon))
    assert board.year == 2026
    assert board.slots == 2
    assert board.ticks == 2
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


def test_projects_horizon_split_ratios():
    well = well_rect(NOMAD)
    bands = projects_horizon_seats(well)
    assert len(bands) == 3
    assert HORIZON_LABELS == ("This week", "This month", "Someday")
    assert bands[0].x == pytest.approx(well.x)
    assert bands[0].w == pytest.approx(well.w)
    assert bands[0].y == pytest.approx(well.y)
    assert bands[-1].bottom == pytest.approx(well.bottom)
    assert bands[1].y - bands[0].bottom == pytest.approx(HORIZON_GAP)
    assert bands[2].y - bands[1].bottom == pytest.approx(HORIZON_GAP)
    leftover = well.h - HORIZON_GAP * 2
    assert leftover == pytest.approx(sum(band.h for band in bands))
    for band in bands:
        assert band.h == pytest.approx(leftover / 3)
        # Nomad well 110.87 × 129.10 mm: each band 41.30 mm after two 2.6 mm gaps.
        assert band.h / leftover == pytest.approx(1 / 3)
        assert band.h / well.h == pytest.approx(leftover / 3 / well.h)
    assert HORIZON_GAP / well.h == pytest.approx(2.6 / well.h)
    assert well.w == pytest.approx(110.87)
    assert well.h == pytest.approx(129.1)
    assert leftover == pytest.approx(123.9)
    assert bands[0].h == pytest.approx(41.3)


def test_projects_horizon_band_and_slot_seats():
    well = well_rect(NOMAD)
    bands = projects_horizon_seats(well)
    head, lines = projects_horizon_band_seats(bands[0], 2)
    assert len(lines) == 2
    assert head.h == pytest.approx(HORIZON_LABEL_H)
    assert head.x == pytest.approx(bands[0].x + HORIZON_INSET_X)
    assert lines[0].y > head.bottom
    assert lines[0].y - head.bottom == pytest.approx(HORIZON_LABEL_GAP)
    assert lines[1].y - lines[0].bottom == pytest.approx(HORIZON_SLOT_GAP)
    assert lines[-1].bottom <= bands[0].bottom - HORIZON_INSET_Y + 1e-9
    inner_h = bands[0].h - 2 * HORIZON_INSET_Y
    body_h = inner_h - HORIZON_LABEL_H - HORIZON_LABEL_GAP
    assert lines[0].h == pytest.approx((body_h - HORIZON_SLOT_GAP) / 2)
    # Slot ≈ 15.65 mm — name + ticks + one notes rule, not an 8-row roster.
    assert lines[0].h == pytest.approx(15.65)

    three_head, three = projects_horizon_band_seats(bands[1], 3)
    assert len(three) == 3
    assert three_head.h == pytest.approx(head.h)

    name, notes = projects_horizon_slot_seats(lines[0])
    assert name.h == pytest.approx(HORIZON_SLOT_NAME_H)
    assert notes.y == pytest.approx(name.bottom + HORIZON_NOTE_GAP)
    assert notes.h == pytest.approx(PROJECT_NOTE_PITCH)
    assert notes.bottom < lines[0].bottom
    rule, marks = projects_horizon_name_and_ticks(name, 2)
    assert rule.x == pytest.approx(name.x)
    assert marks.right == pytest.approx(name.right)
    assert rule.right < marks.x
    assert marks.w > TICK * 2


def test_projects_horizon_paint():
    board = ProjectsHorizon(year=2026, slots=2, ticks=2)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_horizon(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("This week") == 1
    assert texts.count("This month") == 1
    assert texts.count("Someday") == 1
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts
    assert "TO DO" not in texts
    assert "IN PROGRESS" not in texts
    assert "Now" not in texts
    assert "Next" not in texts
    assert "Later" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 2 * 2

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert p_boxes == []

    status = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert status == []

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert len(outlines) == 3


def test_projects_horizon_knobs():
    board = ProjectsHorizon(year=2026, slots=3, ticks=1)
    plotter = RecordingPlotter()
    paint_projects_horizon(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 3 * 1
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("This week") == 1
    assert "P" not in texts


def test_projects_horizon_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsHorizonSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert HORIZON_SLOTS == 2
    assert HORIZON_TICKS == 2
