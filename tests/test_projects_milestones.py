import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsMilestones
from parch.devices.nomad import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    HAIR,
    MILESTONE_BODY_GAP,
    MILESTONE_DATE_W,
    MILESTONE_HEAD_H,
    MILESTONE_NOTES_GAP,
    MILESTONE_NOTES_H,
    MILESTONE_RUNG_GAP,
    MILESTONE_STATUS_W,
    PROJECT_NOTE_PITCH,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    RULE,
    RULE_C,
    SOFT,
    TICK,
    paint_projects_milestones,
    projects_milestones_head_seats,
    projects_milestones_rung_seats,
    projects_milestones_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_milestones import ProjectsMilestonesSection
from parch.spec import Spec


def test_projects_milestones_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_milestones" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsMilestones) for item in page.components)


def test_projects_milestones_page():
    spec = Spec(notes_pages=1)
    page = ProjectsMilestonesSection(spec).pages()[0]
    assert page.dest == "projects-milestones-2026"
    assert page.kind == "projects_milestones"
    assert page.title == "Projects"
    ladder = next(item for item in page.components if isinstance(item, ProjectsMilestones))
    assert ladder.year == 2026
    assert ladder.rungs == 5
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


def test_projects_milestones_seats_ladder():
    well = well_rect(NOMAD)
    head, rungs, notes = projects_milestones_seats(well, 5)
    assert head.y == pytest.approx(well.y)
    assert head.h == pytest.approx(MILESTONE_HEAD_H)
    assert head.x == pytest.approx(well.x)
    assert head.w == pytest.approx(well.w)
    assert len(rungs) == 5
    assert rungs[0].y == pytest.approx(head.bottom + MILESTONE_BODY_GAP)
    assert rungs[1].y == pytest.approx(rungs[0].bottom + MILESTONE_RUNG_GAP)
    assert rungs[-1].bottom == pytest.approx(notes.y - MILESTONE_NOTES_GAP)
    assert notes.h == pytest.approx(MILESTONE_NOTES_H)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.x == pytest.approx(well.x)
    assert notes.w == pytest.approx(well.w)
    for rung in rungs:
        assert rung.x == pytest.approx(well.x)
        assert rung.w == pytest.approx(well.w)
        assert rung.h == pytest.approx(rungs[0].h)
    leftover = well.h - MILESTONE_HEAD_H - MILESTONE_BODY_GAP - MILESTONE_NOTES_GAP
    assert notes.h / leftover < 0.35
    assert rungs[0].h * 5 > notes.h

    name, status = projects_milestones_head_seats(head)
    assert name.x == pytest.approx(head.x)
    assert status.right == pytest.approx(head.right)
    assert name.right < status.x
    assert status.w == pytest.approx(MILESTONE_STATUS_W)

    tick, name_box, date = projects_milestones_rung_seats(rungs[0])
    assert tick.x == pytest.approx(rungs[0].x)
    assert tick.w == pytest.approx(TICK)
    assert tick.h == pytest.approx(TICK)
    assert name_box.x > tick.right
    assert name_box.right == pytest.approx(rungs[0].right)
    assert date.x == pytest.approx(name_box.x)
    assert date.w == pytest.approx(MILESTONE_DATE_W)
    assert date.y > name_box.bottom
    assert date.right < name_box.right


def test_projects_milestones_paint_rungs_dates_and_status():
    ladder = ProjectsMilestones(year=2026, rungs=5)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_milestones(plotter, well, ladder)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    assert texts.count("Doing") == 1
    assert texts.count("Done") == 1
    assert texts.count("Next") == 1
    for rejected in (
        "PROJECT",
        "Focus",
        "Notes",
        "TO DO",
        "IN PROGRESS",
        "DONE!",
        "Week",
        "Meeting",
        "Parking lot",
        "Active",
    ):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 5

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 3

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 1

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    date_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(MILESTONE_DATE_W)
    ]
    assert len(date_rules) == 5

    _, rungs, notes = projects_milestones_seats(well, 5)
    name_w = projects_milestones_rung_seats(rungs[0])[1].w
    name_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(name_w)
    ]
    assert len(name_rules) == 5

    spines = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(HAIR)
        and op[6] == pytest.approx(SOFT)
        and op[1] == pytest.approx(op[3])
    ]
    assert len(spines) == 1

    notes_outline = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(notes.w)
        and op[1].h == pytest.approx(notes.h)
    ]
    assert len(notes_outline) == 1

    note_inset_w = notes.w - 2.2
    note_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(note_inset_w)
    ]
    assert len(note_rules) >= 4
    assert all(op[2] > notes.y for op in note_rules)

    card_outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert card_outlines == notes_outline


def test_projects_milestones_knobs():
    spec = Spec(notes_pages=1, project_milestones=4)
    page = ProjectsMilestonesSection(spec).pages()[0]
    ladder = next(item for item in page.components if isinstance(item, ProjectsMilestones))
    assert ladder.rungs == 4
    well = well_rect(NOMAD)
    _, rungs, _ = projects_milestones_seats(well, ladder.rungs)
    assert len(rungs) == 4
    plotter = RecordingPlotter()
    paint_projects_milestones(plotter, well, ladder)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4
    date_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(MILESTONE_DATE_W)
    ]
    assert len(date_rules) == 4
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 1


def test_projects_milestones_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsMilestonesSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts


def test_projects_milestones_note_pitch_matches_daily():
    assert PROJECT_NOTE_PITCH == pytest.approx(4.15)
