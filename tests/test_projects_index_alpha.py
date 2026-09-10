import pytest

from parch.books import YearPlanner
from parch.components import ProjectLeaf, ProjectsBoard, ProjectsIndexAlpha
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    INDEX_ALPHA_BAND_GAP,
    INDEX_ALPHA_COL_GAP,
    INDEX_ALPHA_ENTRY_H,
    INDEX_ALPHA_HINT_W,
    INDEX_ALPHA_LETTER_H,
    INDEX_ALPHA_NAME_W,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    TICK,
    paint_projects,
    paint_projects_index_alpha,
    projects_index_alpha_bands,
    projects_index_alpha_band_height,
    projects_index_alpha_columns,
    projects_index_alpha_entry_seats,
    projects_index_alpha_groups,
    projects_index_alpha_letter_and_rows,
    projects_index_alpha_split,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_index_alpha import ProjectsIndexAlphaSection, alpha_entries
from parch.spec import Spec


def _index_pages(spec: Spec | None = None) -> list:
    return ProjectsIndexAlphaSection(spec or Spec(notes_pages=1)).pages()


def test_index_alpha_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_index_alpha" not in kinds
    assert "project" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsIndexAlpha) for item in page.components)
    texts = []
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Proj" not in texts
    assert "Archive" not in texts


def test_projects_index_alpha_page_and_leaves():
    spec = Spec(notes_pages=1)
    pages = _index_pages(spec)
    index = pages[0]
    assert index.dest == "projects-index-alpha-2026"
    assert index.kind == "projects_index_alpha"
    assert index.title == "Projects"
    board = next(item for item in index.components if isinstance(item, ProjectsIndexAlpha))
    assert board.year == 2026
    assert board.index_dest == spec.projects_index_alpha_dest
    assert len(board.entries) == 23
    assert board.entries[0].name == "Archive"
    assert board.entries[0].letter == "A"
    assert board.entries[0].dest == "project-2026-archive"
    assert board.entries[0].hint == "01"
    assert board.entries[-1].name == "Well"
    assert board.entries[-1].hint == "23"
    assert [e.letter for e in board.entries] == sorted(e.letter for e in board.entries)

    leaves = [p for p in pages if p.kind == "project"]
    assert len(leaves) == 23
    assert leaves[0].dest == "project-2026-archive"
    assert leaves[0].title == "Archive"
    leaf = next(item for item in leaves[0].components if isinstance(item, ProjectLeaf))
    assert leaf.index_dest == spec.projects_index_alpha_dest
    assert leaf.hint == "01"
    assert leaf.tasks == 4
    board_one = next(item for item in leaves[0].components if isinstance(item, ProjectsBoard))
    assert board_one.cards == 1


def test_proj_tab_lands_on_index():
    spec = Spec(notes_pages=1)
    pages = _index_pages(spec)
    index = pages[0]
    assert strip_active(index.kind) == "Proj"
    assert strip_items(index) == (
        ("Year", "year-2026"),
        ("Proj", "projects-index-alpha-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
    )
    leaf = pages[1]
    assert strip_active(leaf.kind) == "Proj"
    items = dict(strip_items(leaf))
    assert items["Proj"] == spec.projects_index_alpha_dest


def test_default_strip_still_seven_tabs():
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    labels = [label for label, _ in strip_items(page)]
    assert labels == ["Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"]
    assert strip_active(page.kind) == ""


def test_index_alpha_column_split_and_seats():
    spec = Spec(notes_pages=1)
    entries = alpha_entries(spec)
    groups = projects_index_alpha_groups(entries)
    assert [letter for letter, _ in groups] == [
        "A",
        "B",
        "C",
        "D",
        "F",
        "H",
        "K",
        "L",
        "M",
        "N",
        "P",
        "S",
        "T",
        "W",
    ]
    assert len(groups[0][1]) == 2
    left, right = projects_index_alpha_split(groups)
    assert [letter for letter, _ in left] == ["A", "B", "C", "D", "F", "H", "K"]
    assert [letter for letter, _ in right] == ["L", "M", "N", "P", "S", "T", "W"]
    left_w = sum(1 + len(items) for _, items in left)
    right_w = sum(1 + len(items) for _, items in right)
    assert abs(left_w - right_w) <= 1

    well = well_rect(NOMAD)
    col_l, col_r = projects_index_alpha_columns(well)
    assert col_l.x == pytest.approx(well.x)
    assert col_r.right == pytest.approx(well.right)
    assert col_r.x - col_l.right == pytest.approx(INDEX_ALPHA_COL_GAP)
    assert col_l.w == pytest.approx(col_r.w)

    bands = projects_index_alpha_bands(col_l, left)
    assert len(bands) == len(left)
    assert bands[0].y == pytest.approx(col_l.y)
    assert bands[-1].bottom < col_l.bottom
    assert bands[0].h == pytest.approx(projects_index_alpha_band_height(2))
    assert bands[3].h == pytest.approx(projects_index_alpha_band_height(1))
    assert bands[1].y - bands[0].bottom == pytest.approx(INDEX_ALPHA_BAND_GAP)

    cap, rows = projects_index_alpha_letter_and_rows(bands[0], 2)
    assert cap.h == pytest.approx(INDEX_ALPHA_LETTER_H)
    assert len(rows) == 2
    assert rows[0].y > cap.bottom
    assert rows[-1].bottom == pytest.approx(bands[0].bottom)
    assert rows[0].h == pytest.approx(INDEX_ALPHA_ENTRY_H)

    name, leaders, hint = projects_index_alpha_entry_seats(rows[0])
    assert name.x == pytest.approx(rows[0].x)
    assert name.w == pytest.approx(INDEX_ALPHA_NAME_W)
    assert hint.w == pytest.approx(INDEX_ALPHA_HINT_W)
    assert hint.right == pytest.approx(rows[0].right)
    assert name.right == pytest.approx(leaders.x)
    assert leaders.right == pytest.approx(hint.x)
    assert leaders.w > 8


def test_index_alpha_paint_is_book_not_kanban():
    spec = Spec(notes_pages=1)
    page = _index_pages(spec)[0]
    board = next(item for item in page.components if isinstance(item, ProjectsIndexAlpha))
    plotter = RecordingPlotter()
    paint_projects_index_alpha(plotter, well_rect(NOMAD), board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Archive" in texts
    assert "Well" in texts
    assert texts.count("A") == 1
    assert texts.count("W") == 1
    assert "01" in texts
    assert "23" in texts
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "PROJECT" not in texts
    assert "Focus" not in texts

    letters = [op for op in plotter.ops if op[0] == "text" and op[2] in {g[0] for g in projects_index_alpha_groups(board.entries)}]
    assert all(op[8] for op in letters)
    assert all(op[6] == "sans" for op in letters)
    names = [op for op in plotter.ops if op[0] == "text" and op[2] in {e.name for e in board.entries}]
    assert all(op[6] == "serif" for op in names)
    hints = [op for op in plotter.ops if op[0] == "text" and op[2] in {e.hint for e in board.entries}]
    assert all(op[8] for op in hints)

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []
    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert p_boxes == []
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    links = plotter.links()
    assert len(links) == 23
    assert "project-2026-archive" in links
    assert "project-2026-well" in links
    assert spec.projects_index_alpha_dest not in links


def test_index_and_leaves_link_both_ways():
    spec = Spec(notes_pages=1)
    pages = _index_pages(spec)
    plotter = RecordingPlotter()
    for page in pages:
        plotter.reserve_dest(page.dest)
    for page in pages:
        plotter.begin_page()
        plotter.add_dest(page.dest)
        PlannerLayout().paint(page, plotter, NOMAD)

    dests = plotter.dests()
    assert dests[0] == spec.projects_index_alpha_dest
    assert "project-2026-archive" in dests
    assert "project-2026-nomad" in dests

    links = plotter.links()
    for entry in alpha_entries(spec):
        assert entry.dest in links
    assert links.count(spec.projects_index_alpha_dest) >= 23

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "A–Z" in texts
    assert "Index" in texts
    assert texts.count("Proj") >= 2
    assert "Archive" in texts


def test_project_leaf_reuses_card_craft():
    spec = Spec(notes_pages=1)
    page = next(p for p in _index_pages(spec) if p.dest == "project-2026-archive")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    plotter = RecordingPlotter()
    paint_projects(plotter, Rect(4, 20, 110, 90), board)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4
    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 3


def test_index_alpha_header_and_proj_active():
    spec = Spec(notes_pages=1)
    page = _index_pages(spec)[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "A–Z" in texts
    assert "Proj" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert strip_active(page.kind) == "Proj"
