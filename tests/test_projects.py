import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsIndex
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.fonts import JostBodyRamp
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_ICON,
    CLONE_ICONS,
    CLONE_P_PAD,
    CLONE_RAIL_SLOT_GAP,
    CLONE_SPINE_W,
    CLONE_STATUS_LABELS,
    CLONE_STRIP_H,
    CLONE_TRACK_H,
    MUTED,
    PROJECT_COL_WEIGHTS,
    PROJECT_P,
    PROJECT_STATUS_H,
    PROJECT_STATUS_MARK,
    TICK,
    TICKET_BODY_GAP,
    TICKET_GAP,
    TICKET_MARK,
    TICKET_NAME_WEIGHTS,
    TICKET_PREVIEW_GAP,
    TICKET_STRIP_GRAY,
    TICKET_STRIP_LEFT,
    TICKET_STRIP_PAD,
    TICKET_STUB_W,
    clone_task_count,
    paint_project,
    paint_projects_index,
    project_card_columns,
    project_card_left_seats,
    project_card_seats,
    project_ticket_body_seats,
    project_ticket_link_hits,
    project_ticket_name_seats,
    project_ticket_parts,
    project_ticket_preview_cards,
    project_ticket_seats,
    projects_clone_a_card,
    projects_clone_a_seats,
    projects_clone_a_well,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec
from parch.tracks import rows


def _rects_overlap(a: Rect, b: Rect) -> bool:
    return a.x < b.right and b.x < a.right and a.y < b.bottom and b.y < a.bottom


_PROJ_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meetings-index-2026"),
    ("Task", "tasks-index-2026-Q1"),
    ("Rev", "review-index-2026"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_projects_page_after_annual():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert pages[1].dest == "year-2026"
    page = pages[2]
    assert page.dest == "projects-index-2026-01"
    assert page.kind == "projects_index"
    assert page.title == "Projects"
    assert pages[3].dest == "projects-2026-01"
    assert pages[11].dest == "meetings-index-2026"
    assert pages[28].dest == "tasks-index-2026-Q1"
    assert pages[85].dest == "review-index-2026"
    assert pages[139].dest == "quarter-2026-Q1"
    assert not any(p.kind == "projects" for p in pages)

    roster = next(item for item in page.components if isinstance(item, ProjectsIndex))
    assert roster.year == 2026
    assert len(roster.tickets) == 8

    assert strip_active(page.kind) == "Proj"
    assert strip_items(page) == _PROJ_STRIP


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


def test_projects_knobs_from_spec():
    spec = Spec(notes_pages=1, project_cards=2, project_tasks=5)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "project")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    assert board.cards == 2
    assert board.tasks == 5
    plotter = RecordingPlotter()
    paint_project(plotter, Rect(4, 20, 110, 90), board, body=JostBodyRamp())
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 2


def test_projects_header_year_and_tabs():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects_index")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Rev", "Week", "Day", "Notes"):
        assert label in texts


def test_projects_index_tickets_and_proj_nav():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2] == "projects-index-2026-01"
    assert dests[3:11] == [f"projects-2026-{slot:02d}" for slot in range(1, 9)]
    assert dests[11] == "meetings-index-2026"
    assert dests[12:28] == [f"meeting-2026-{slot:02d}" for slot in range(1, 17)]
    assert dests[28] == "tasks-index-2026-Q1"
    assert dests[139] == "quarter-2026-Q1"

    index = pages[2]
    assert index.kind == "projects_index"
    assert index.title == "Projects"
    assert strip_active(index.kind) == "Proj"
    assert strip_items(index) == _PROJ_STRIP

    roster = next(item for item in index.components if isinstance(item, ProjectsIndex))
    assert roster.year == 2026
    assert roster.dest == "projects-index-2026-01"
    assert len(roster.tickets) == 8
    assert [ticket.dest for ticket in roster.tickets] == [
        f"projects-2026-{slot:02d}" for slot in range(1, 9)
    ]
    assert [ticket.number for ticket in roster.tickets] == list(range(1, 9))

    leaf = next(page for page in pages if page.dest == "projects-2026-03")
    assert leaf.kind == "project"
    assert leaf.title == "Projects"
    assert strip_active(leaf.kind) == "Proj"
    assert ("Proj", "projects-index-2026-01") in strip_items(leaf)
    board = next(item for item in leaf.components if isinstance(item, ProjectsBoard))
    assert board.cards == 3
    assert board.number == 3
    assert board.index_dest == "projects-index-2026-01"
    assert board.tasks == 4


def test_project_ticket_seats():
    well = Rect(4, 20, 110, 90)
    seats = project_ticket_seats(well, 8)
    assert len(seats) == 8
    assert seats[0].y == pytest.approx(well.y)
    assert seats[0].x == pytest.approx(well.x)
    assert seats[0].w == pytest.approx(well.w)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    assert seats[1].y > seats[0].bottom
    leftover = well.h - TICKET_GAP * 7
    assert seats[0].h == pytest.approx(leftover / 8)

    stub, body = project_ticket_parts(seats[0])
    assert stub.x > seats[0].x
    assert body.right < seats[0].right
    assert stub.right == pytest.approx(body.x)
    assert stub.w == pytest.approx(TICKET_STUB_W)

    name, preview = project_ticket_body_seats(body)
    assert name.x == pytest.approx(body.x)
    assert preview.right == pytest.approx(body.right)
    assert name.right < preview.x
    share = name.w + preview.w
    assert name.w / share == pytest.approx(TICKET_NAME_WEIGHTS[0] / sum(TICKET_NAME_WEIGHTS))
    leftover = body.w - TICKET_BODY_GAP
    assert name.w == pytest.approx(leftover * TICKET_NAME_WEIGHTS[0] / sum(TICKET_NAME_WEIGHTS))
    assert preview.w == pytest.approx(leftover * TICKET_NAME_WEIGHTS[1] / sum(TICKET_NAME_WEIGHTS))
    assert preview.w / leftover == pytest.approx(0.45)

    cards = project_ticket_preview_cards(preview)
    assert len(cards) == 3
    assert cards[0].y > preview.y
    assert cards[-1].bottom < preview.bottom
    assert cards[0].x > preview.x
    assert cards[-1].right < preview.right
    assert cards[1].x > cards[0].right
    assert cards[2].x > cards[1].right
    assert cards[1].x - cards[0].right == pytest.approx(TICKET_PREVIEW_GAP)
    assert cards[2].x - cards[1].right == pytest.approx(TICKET_PREVIEW_GAP)
    assert TICKET_PREVIEW_GAP == pytest.approx(1.4)
    assert cards[0].y == pytest.approx(cards[1].y)
    assert cards[0].h == pytest.approx(cards[1].h)

    write, strip = project_ticket_name_seats(name)
    assert strip.h == pytest.approx(CLONE_STRIP_H)
    assert write.bottom + TICKET_STRIP_PAD == pytest.approx(strip.y)
    assert strip.x == pytest.approx(name.x + TICKET_STRIP_LEFT)
    assert strip.w == pytest.approx(name.w - TICKET_STRIP_LEFT)
    assert TICKET_STRIP_LEFT == pytest.approx(0.30)
    assert write.right == pytest.approx(name.right)
    assert write.right < preview.x
    assert CLONE_ICON == pytest.approx(2.1)
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

    nomad = project_ticket_seats(well_rect(NOMAD), 8)[0]
    nstub, nbody = project_ticket_parts(nomad)
    nname, _npreview = project_ticket_body_seats(nbody)
    nwrite, nstrip = project_ticket_name_seats(nname)
    stub_mark_bottom = nstub.y + (nstub.h + TICKET_MARK) / 2
    assert nwrite.bottom >= stub_mark_bottom - 0.05
    assert nstrip.y > stub_mark_bottom
    assert nwrite.right < _npreview.x


def test_projects_index_paint_write_in_underlines_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects_index")
    roster = next(item for item in page.components if isinstance(item, ProjectsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_index(plotter, well, roster, body=JostBodyRamp())

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for slot in range(1, 9):
        assert f"{slot:02d}" in texts
    assert "P" not in texts
    assert "Atlas" not in texts
    assert "Harbor" not in texts
    assert texts.count("Todo") == 0

    stubs = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICKET_MARK)
    ]
    assert len(stubs) == 8

    seats = project_ticket_seats(well, 8)
    rules = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(0.12)
    ]
    assert len(rules) == 8
    for seat, rule in zip(seats, rules, strict=True):
        _, body = project_ticket_parts(seat)
        name, preview = project_ticket_body_seats(body)
        write, strip = project_ticket_name_seats(name)
        assert rule[1] == pytest.approx(write.x)
        assert rule[2] == pytest.approx(write.bottom)
        assert rule[3] == pytest.approx(write.right)
        assert rule[3] < preview.x
        assert rule[2] < strip.y

    painted = [op[1] for op in plotter.ops if op[0] == "rect" and op[2] and not op[3]]
    expected: list[Rect] = []
    for seat in seats:
        _, body = project_ticket_parts(seat)
        _, preview = project_ticket_body_seats(body)
        expected.extend(project_ticket_preview_cards(preview))
    assert len(expected) == 8 * 3
    for card in expected:
        assert any(
            box.x == pytest.approx(card.x)
            and box.y == pytest.approx(card.y)
            and box.w == pytest.approx(card.w)
            and box.h == pytest.approx(card.h)
            for box in painted
        )

    link_ops = [op for op in plotter.ops if op[0] == "link"]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, ticket in zip(seats, roster.tickets, strict=True):
        hits = project_ticket_link_hits(seat)
        assert len(hits) == 4
        stub, body = project_ticket_parts(seat)
        name, preview = project_ticket_body_seats(body)
        write, strip = project_ticket_name_seats(name)
        cards = project_ticket_preview_cards(preview)
        assert hits[0] == stub
        assert hits[1:] == cards
        for hit in hits:
            assert not _rects_overlap(hit, write)
            assert not _rects_overlap(hit, strip)
        expected_hits.extend((hit, ticket.dest) for hit in hits)
    assert [(op[1], op[2]) for op in link_ops] == expected_hits
    assert [dest for _, dest in expected_hits] == [
        dest for slot in range(1, 9) for dest in (f"projects-2026-{slot:02d}",) * 4
    ]
    for seat in seats:
        assert all(op[1] != seat for op in link_ops)
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert len(fills) >= 8 * len(CLONE_ICONS)
    assert all(op[5] == pytest.approx(TICKET_STRIP_GRAY) for op in fills)
    assert TICKET_STRIP_GRAY == pytest.approx(198 / 255)

    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    chrome_texts = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Projects" in chrome_texts
    assert "Proj" in chrome_texts
    assert "Atlas" not in chrome_texts
    assert "Harbor" not in chrome_texts


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

    nomad = well_rect(NOMAD)
    _, nrails = projects_clone_a_seats(nomad, 3)
    nrail = nrails[0]
    track_h = min(CLONE_TRACK_H, nrail.h - 2.0)
    track = Rect(nrail.x, nrail.y + (nrail.h - track_h) / 2, nrail.w, track_h)
    inset = track.inset(1.4, 0.6)
    slots = rows(inset, 3, gap=CLONE_RAIL_SLOT_GAP)
    marks = [
        Rect(
            slot.x,
            slot.y + (slot.h - PROJECT_STATUS_MARK) / 2,
            PROJECT_STATUS_MARK,
            PROJECT_STATUS_MARK,
        )
        for slot in slots
    ]
    assert CLONE_STATUS_LABELS == ("Todo", "In Progress", "Done")
    assert marks[1].y - marks[0].bottom == pytest.approx(
        slots[0].h + CLONE_RAIL_SLOT_GAP - PROJECT_STATUS_MARK
    )
    assert marks[1].y - marks[0].bottom > 5.0
    assert marks[2].y - marks[1].bottom > 5.0


def test_project_page_g_clone_and_index_chip():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "projects-2026-01")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    assert board.number == 1
    well = well_rect(NOMAD)
    ink = RecordingPlotter()
    paint_project(ink, well, board, body=JostBodyRamp())
    texts = [op[2] for op in ink.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert "Atlas" not in texts
    assert texts.count("Todo") == 3
    assert texts.count("In Progress") == 3
    assert texts.count("Done") == 3
    assert "Doing" not in texts
    p_texts = [op for op in ink.ops if op[0] == "text" and op[2] == "P"]
    assert all(op[7] == pytest.approx(MUTED) for op in p_texts)
    assert all(op[3] == pytest.approx(JostBodyRamp().ink("caption").size) for op in p_texts)
    ticks = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    _, _, _, tasks, _, _ = projects_clone_a_card(projects_clone_a_seats(well, 3)[0][0])
    assert len(ticks) == 3 * clone_task_count(tasks)
    assert clone_task_count(tasks) > 4
    spines = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[3] and op[1].w == pytest.approx(CLONE_SPINE_W)
    ]
    assert len(spines) == 3
    dots = [
        op
        for op in ink.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(CLONE_DOT)
        and op[1].h == pytest.approx(CLONE_DOT)
    ]
    assert len(dots) > 30
    assert all(op[5] == pytest.approx(198 / 255) for op in dots)
    assert CLONE_STATUS_LABELS == ("Todo", "In Progress", "Done")
    p_boxes = [
        op[1]
        for op in ink.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 3
    for mark, text in zip(p_boxes, p_texts, strict=True):
        label = text[1]
        assert label.x >= mark.x + CLONE_P_PAD - 0.01
        assert label.y >= mark.y + CLONE_P_PAD - 0.01

    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Projects" in labels
    assert "Atlas" not in labels
    assert "01" in labels
    assert "Index" not in labels
    assert "Proj" in labels
    assert "In Progress" in labels
    assert strip_active(page.kind) == "Proj"
    assert dict(strip_items(page))["Proj"] == spec.projects_index_dest
    assert spec.projects_index_dest == "projects-index-2026-01"
    leaf_links = [op[2] for op in chrome.ops if op[0] == "link"]
    chip_links = [dest for dest in leaf_links if dest == spec.projects_index_dest]
    assert len(chip_links) >= 2
    assert "projects-2026" not in leaf_links


def test_projects_tickets_knob():
    spec = Spec(notes_pages=1, project_tickets=6)
    pages = YearPlanner().pages(spec)
    roster = next(
        item
        for page in pages
        if page.kind == "projects_index"
        for item in page.components
        if isinstance(item, ProjectsIndex)
    )
    assert len(roster.tickets) == 6
    dests = [page.dest for page in pages]
    assert "projects-2026-06" in dests
    assert "projects-2026-07" not in dests
    plotter = RecordingPlotter()
    paint_projects_index(plotter, Rect(4, 20, 110, 90), roster, body=JostBodyRamp())
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Field" not in texts
    assert "Grove" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        dest for slot in range(1, 7) for dest in (f"projects-2026-{slot:02d}",) * 4
    ]


def test_projects_index_pages_knob():
    spec = Spec(notes_pages=1, project_index_pages=3)
    assert spec.project_count == 24
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2:5] == [
        "projects-index-2026-01",
        "projects-index-2026-02",
        "projects-index-2026-03",
    ]
    assert dests[5:29] == [f"projects-2026-{slot:02d}" for slot in range(1, 25)]
    assert dests[29] == "meetings-index-2026"
    assert dests[157] == "quarter-2026-Q1"

    indexes = [page for page in pages if page.kind == "projects_index"]
    assert len(indexes) == 3
    slices = [
        [
            ticket.number
            for ticket in next(
                item for item in page.components if isinstance(item, ProjectsIndex)
            ).tickets
        ]
        for page in indexes
    ]
    assert slices == [list(range(1, 9)), list(range(9, 17)), list(range(17, 25))]

    page_two = next(item for item in indexes[1].components if isinstance(item, ProjectsIndex))
    plotter = RecordingPlotter()
    paint_projects_index(plotter, well_rect(NOMAD), page_two, body=JostBodyRamp())
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "09" in texts
    assert "16" in texts
    assert "01" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        dest for slot in range(9, 17) for dest in (f"projects-2026-{slot:02d}",) * 4
    ]

    leaf = next(page for page in pages if page.dest == "projects-2026-10")
    board = next(item for item in leaf.components if isinstance(item, ProjectsBoard))
    assert board.number == 10
    assert board.index_dest == "projects-index-2026-02"
    assert dict(strip_items(leaf))["Proj"] == "projects-index-2026-02"
    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(leaf, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "10" in labels
    assert "Index" not in labels
    assert "projects-index-2026-02" in [op[2] for op in chrome.ops if op[0] == "link"]
    assert "projects-index-2026-01" not in [op[2] for op in chrome.ops if op[0] == "link"]

    year = next(page for page in pages if page.kind == "annual")
    assert dict(strip_items(year))["Proj"] == spec.projects_index_dest
    assert spec.projects_index_dest == "projects-index-2026-01"
