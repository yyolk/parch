import pytest

from parch.books import YearPlanner
from parch.components import ProjectSheet, ProjectsBoard, ProjectsIndex
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    COVER_INSET,
    COVER_LINE_PAD,
    COVER_LINE_PITCH,
    COVER_QUAD_GAP,
    COVER_RULE_INSET,
    HAIR,
    INK,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    TICK,
    paint_project_sheet,
    paint_projects,
    paint_projects_index_covers,
    projects_index_cover_quads,
    projects_index_covers,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_projects_index_follows_board_then_sheets():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2:10] == [
        "projects-2026",
        "projects-index-2026",
        "projects-2026-01",
        "projects-2026-02",
        "projects-2026-03",
        "projects-2026-04",
        "projects-2026-05",
        "projects-2026-06",
    ]
    assert dests[10] == "quarter-2026-Q1"

    index = next(page for page in pages if page.kind == "projects_index")
    assert index.dest == "projects-index-2026"
    assert index.title == "Projects"
    assert strip_active(index.kind) == "Proj"
    assert ("Proj", "projects-index-2026") in strip_items(index)
    grid = next(item for item in index.components if isinstance(item, ProjectsIndex))
    assert grid.year == 2026
    assert grid.dests == tuple(f"projects-2026-{n:02d}" for n in range(1, 7))
    assert grid.titles == tuple(f"Project {n:02d}" for n in range(1, 7))

    sheet = next(page for page in pages if page.dest == "projects-2026-03")
    assert sheet.kind == "project"
    assert sheet.title == "Project"
    assert strip_active(sheet.kind) == "Proj"
    assert dict(strip_items(sheet))["Proj"] == "projects-index-2026"
    card = next(item for item in sheet.components if isinstance(item, ProjectSheet))
    assert card.number == 3
    assert card.title == "Project 03"
    assert card.tasks == 4
    assert card.index_dest == "projects-index-2026"


def test_proj_chip_lands_on_index_from_other_pages():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)

    def proj(dest: str) -> str:
        page = next(p for p in pages if p.dest == dest)
        return dict(strip_items(page))["Proj"]

    assert proj("year-2026") == "projects-index-2026"
    assert proj("projects-2026") == "projects-index-2026"
    assert proj("projects-index-2026") == "projects-index-2026"
    assert proj("projects-2026-01") == "projects-index-2026"
    assert proj("quarter-2026-Q3") == "projects-index-2026"
    assert proj("month-2026-07") == "projects-index-2026"
    assert proj("month-2026-07-habits") == "projects-index-2026"
    assert proj("week-2026-W01") == "projects-index-2026"
    assert proj("2026-07-15") == "projects-index-2026"
    assert proj("2026-07-15-notes-1") == "projects-index-2026"


def test_projects_index_cover_tracks():
    well = Rect(4, 20, 110, 90)
    seats = projects_index_covers(well, 6)
    assert len(seats) == 6
    assert seats[0].x == pytest.approx(well.x)
    assert seats[0].y == pytest.approx(well.y)
    assert seats[1].x > seats[0].right
    assert seats[1].y == pytest.approx(seats[0].y)
    assert seats[2].y > seats[0].bottom
    assert seats[2].x == pytest.approx(seats[0].x)
    assert seats[5].right == pytest.approx(well.right)
    assert seats[5].bottom == pytest.approx(well.bottom)
    assert seats[0].w == pytest.approx(seats[1].w)
    assert seats[0].h == pytest.approx(seats[2].h)

    eight = projects_index_covers(well, 8)
    assert len(eight) == 8
    assert eight[6].y > eight[4].bottom
    assert eight[-1].bottom == pytest.approx(well.bottom)
    with pytest.raises(ValueError, match="slots"):
        projects_index_covers(well, 4)


def test_projects_index_cover_quads_are_two_by_two():
    cover = Rect(4, 20, 50, 40)
    ul, ur, ll, lr = projects_index_cover_quads(cover)
    inset = cover.inset(COVER_INSET)
    assert ul.x == pytest.approx(inset.x)
    assert ul.y == pytest.approx(inset.y)
    assert ur.x > ul.right
    assert ur.y == pytest.approx(ul.y)
    assert ll.x == pytest.approx(ul.x)
    assert ll.y > ul.bottom
    assert lr.x == pytest.approx(ur.x)
    assert lr.y == pytest.approx(ll.y)
    assert ur.right == pytest.approx(inset.right)
    assert ll.bottom == pytest.approx(inset.bottom)
    assert lr.right == pytest.approx(inset.right)
    assert lr.bottom == pytest.approx(inset.bottom)
    assert ur.x - ul.right == pytest.approx(COVER_QUAD_GAP)
    assert ll.y - ul.bottom == pytest.approx(COVER_QUAD_GAP)


def _writein_line_count(box: Rect) -> int:
    n = 0
    y = box.y + COVER_LINE_PAD
    while y < box.bottom - 0.3:
        n += 1
        y += COVER_LINE_PITCH
    return n


def test_paint_projects_index_covers_writein_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects_index")
    index = next(item for item in page.components if isinstance(item, ProjectsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_index_covers(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts == []
    for n in range(1, 7):
        assert f"Project {n:02d}" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Atlas" not in texts

    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[6] == pytest.approx(INK)
    ]
    assert len(frames) == 6 * 5

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    seats = projects_index_covers(well, 6)
    expected_lines = sum(_writein_line_count(projects_index_cover_quads(c)[0]) for c in seats)
    lines = [op for op in plotter.ops if op[0] == "line"]
    assert len(lines) == expected_lines
    assert expected_lines > 6
    for cover in seats:
        ul, ur, ll, lr = projects_index_cover_quads(cover)
        assert ul.right < ur.x
        assert ul.bottom < ll.y
        cover_lines = [op for op in lines if ul.x <= op[1] < ul.right]
        assert len(cover_lines) == _writein_line_count(ul)
        for line in cover_lines:
            assert line[1] == pytest.approx(ul.x + COVER_RULE_INSET)
            assert line[3] == pytest.approx(ul.right - COVER_RULE_INSET)
            assert ul.y < line[2] < ul.bottom

    links = plotter.links()
    assert links == list(index.dests)


def test_index_slots_eight_is_two_by_four():
    spec = Spec(notes_pages=1, project_index_slots=8)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects_index")
    index = next(item for item in page.components if isinstance(item, ProjectsIndex))
    assert len(index.dests) == 8
    assert index.dests[-1] == "projects-2026-08"
    assert index.titles[-1] == "Project 08"
    well = well_rect(NOMAD)
    seats = projects_index_covers(well, 8)
    assert len(seats) == 8
    plotter = RecordingPlotter()
    paint_projects_index_covers(plotter, well, index)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts == []
    assert "Project 08" not in texts
    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[6] == pytest.approx(INK)
    ]
    assert len(frames) == 8 * 5
    expected_lines = sum(_writein_line_count(projects_index_cover_quads(c)[0]) for c in seats)
    assert len([op for op in plotter.ops if op[0] == "line"]) == expected_lines
    assert plotter.links() == list(index.dests)


def test_spec_titles_are_not_printed_on_covers():
    spec = Spec(
        notes_pages=1,
        project_titles=("Atlas", "Harbor", "Keel", "Nomad", "Quarry", "Ridge"),
    )
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects_index")
    index = next(item for item in page.components if isinstance(item, ProjectsIndex))
    assert index.titles == ("Atlas", "Harbor", "Keel", "Nomad", "Quarry", "Ridge")
    plotter = RecordingPlotter()
    paint_projects_index_covers(plotter, well_rect(NOMAD), index)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for title in index.titles:
        assert title not in texts
    leaf = next(p for p in YearPlanner().pages(spec) if p.dest == "projects-2026-02")
    assert leaf.title == "Project"


def test_project_sheet_reuses_g_card_and_links_home():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "projects-2026-01")
    sheet = next(item for item in page.components if isinstance(item, ProjectSheet))
    well = well_rect(NOMAD)
    ink = RecordingPlotter()
    paint_project_sheet(ink, well, sheet)
    texts = [op[2] for op in ink.ops if op[0] == "text"]
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    assert "Doing" in texts and "Done" in texts
    ticks = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4
    p_boxes = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 1
    marks = [
        op
        for op in ink.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 3

    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    texts = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Project" in texts
    assert "Project 01" not in texts
    assert "01" in texts
    assert "Index" in texts
    assert "Proj" in texts
    assert "projects-index-2026" in chrome.links()


def test_index_header_projects_and_year():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects_index")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    assert "Proj" in texts
    for n in range(1, 7):
        assert f"Project {n:02d}" not in texts
        assert f"projects-2026-{n:02d}" in plotter.links()


def test_stacked_board_painter_unchanged():
    board = ProjectsBoard(year=2026, cards=3, tasks=4)
    plotter = RecordingPlotter()
    paint_projects(plotter, Rect(4, 20, 110, 90), board)
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 3
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 12


def test_cover_quads_sit_inside_the_cover():
    well = Rect(4, 20, 110, 90)
    cover = projects_index_covers(well, 6)[0]
    ul, ur, ll, lr = projects_index_cover_quads(cover)
    for quad in (ul, ur, ll, lr):
        assert quad.x > cover.x
        assert quad.y > cover.y
        assert quad.right < cover.right
        assert quad.bottom < cover.bottom
    assert HAIR == pytest.approx(0.18)
