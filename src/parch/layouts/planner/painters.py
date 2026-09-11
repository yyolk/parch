"""Painters take ``plotter: Plotter``. Components never draw themselves."""

import math
from datetime import date, timedelta

from parch.calendar import MONTH_NAMES, WEEKDAY_LABELS, short_date_range
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    CoverTitle,
    HabitGrid,
    MeetingAgenda,
    MeetingIndex,
    MonthGrid,
    Notes,
    Priorities,
    ProjectTicket,
    ProjectsBoard,
    ProjectsIndex,
    QuarterGrid,
    ReviewDay,
    ReviewIndex,
    ReviewWeek,
    ReviewWeekPage,
    Schedule,
    TaskWeek,
    TasksIndex,
    TasksWeekPage,
    WeekStrip,
)
from parch.devices.nomad import Device
from parch.fonts.catalog import TypeWeight
from parch.fonts.ramp import BodyRamp, ChromeRamp, TypeInk
from parch.geom import Rect
from parch.plotter.protocol import Plotter, TextAlign
from parch.sections.page import NavItem, Page
from parch.tracks import columns, rows

HAIR = 0.18
RULE = 0.12
INK = 0.0
MUTED = 112 / 255
GHOST = 168 / 255
WASH = 236 / 255
SOFT = 210 / 255
RULE_C = 198 / 255
PAPER = 1.0

HEADER_H = 9.0
NAV_H = 8.0


def _ink_text(
    plotter: Plotter,
    box: Rect,
    content: str,
    ink: TypeInk,
    *,
    gray: float = INK,
    align: TextAlign = "left",
    small_caps: bool = False,
    weight: TypeWeight | None = None,
) -> None:
    """Pass resolved ramp ink through to ``Plotter.text``."""
    plotter.text(
        box,
        content,
        size=ink.size,
        family=ink.family,
        weight=ink.weight if weight is None else weight,
        gray=gray,
        align=align,
        small_caps=small_caps,
    )


def paint_toolbar(_plotter: Plotter, _device: Device) -> None:
    """Nomad top 8 mm stays reserved and unmarked. No fill, no label."""


def paint_header(
    plotter: Plotter,
    device: Device,
    title: str,
    meta: str,
    meta_dest: str | None = None,
    *,
    chrome: ChromeRamp,
    chip: str = "",
    chip_dest: str | None = None,
) -> None:
    slab = Rect(0.0, device.content_top, device.page_width, HEADER_H)
    plotter.rect(slab, stroke=False, fill=True, fill_gray=INK)
    gutter = device.writing_clearance
    meta_w = 18.0
    chip_w = 16.0 if chip else 0.0
    title_box = Rect(
        gutter, slab.y, device.page_width - 2 * gutter - meta_w - chip_w - 1.5, slab.h
    )
    _ink_text(plotter, title_box, title, chrome.ink("page_title"), gray=PAPER)
    slab_ink = chrome.ink("chrome")
    if chip:
        chip_box = Rect(device.page_width - gutter - meta_w - chip_w - 1.2, slab.y, chip_w, slab.h)
        _ink_text(
            plotter,
            chip_box,
            chip,
            slab_ink,
            gray=SOFT,
            align="right",
            small_caps=True,
        )
        if chip_dest:
            plotter.link(chip_box, chip_dest)
    if meta:
        meta_box = Rect(device.page_width - gutter - meta_w, slab.y, meta_w, slab.h)
        _ink_text(
            plotter,
            meta_box,
            meta,
            slab_ink,
            gray=SOFT,
            align="right",
            small_caps=True,
        )
        if meta_dest:
            plotter.link(meta_box, meta_dest)


def paint_nav(
    plotter: Plotter,
    device: Device,
    items: tuple[tuple[str, str], ...],
    active: str,
    *,
    chrome: ChromeRamp,
) -> None:
    if not items:
        return
    y = device.page_height - NAV_H
    slot = device.page_width / len(items)
    plotter.rect(Rect(0.0, y, device.page_width, NAV_H), stroke=False, fill=True, fill_gray=WASH)
    nav = chrome.ink("nav")
    for i, (label, dest) in enumerate(items):
        x = i * slot
        hit = Rect(x, y, slot, NAV_H)
        on = label == active
        if on:
            plotter.rect(hit, stroke=False, fill=True, fill_gray=INK)
        _ink_text(
            plotter,
            hit,
            label,
            nav,
            gray=PAPER if on else INK,
            small_caps=True,
            align="center",
            weight="bold" if on else None,
        )
        plotter.link(hit, dest)
        if i and not on:
            prev_on = items[i - 1][0] == active
            if not prev_on:
                plotter.line(x, y + 1.8, x, y + NAV_H - 1.8, stroke_width=HAIR, stroke_gray=SOFT)


def paint_chrome(
    plotter: Plotter, box: Rect, title: str, nav: tuple[NavItem, ...]
) -> None:
    """Legacy header+chips path — unused after the black-slab / strip nav."""
    _ = (plotter, box, title, nav)


def paint_cover(plotter: Plotter, device: Device, cover: CoverTitle, *, chrome: ChromeRamp) -> None:
    top = device.content_top
    outer, inner = 3.2, 4.6
    # Frame sits below the unmarked toolbar; do not shrink the Nomad page.
    ox, oy = outer, max(outer, top + 0.6)
    plotter.rect(
        Rect(ox, oy, device.page_width - 2 * ox, device.page_height - oy - outer),
        stroke=True,
        fill=False,
        stroke_width=HAIR,
        stroke_gray=INK,
    )
    ix, iy = inner, max(inner, top + 1.8)
    plotter.rect(
        Rect(ix, iy, device.page_width - 2 * ix, device.page_height - iy - inner),
        stroke=True,
        fill=False,
        stroke_width=HAIR,
        stroke_gray=INK,
    )

    brow = Rect(0.0, 38.0, device.page_width, 8.0)
    _ink_text(
        plotter,
        brow,
        "Year Book",
        chrome.ink("cover_brow"),
        gray=MUTED,
        small_caps=True,
        align="center",
    )
    year_box = Rect(0.0, 56.0, device.page_width, 20.0)
    _ink_text(
        plotter,
        year_box,
        str(cover.year),
        chrome.ink("cover_year"),
        align="center",
    )
    tap_w = 48.0
    plotter.link(
        Rect((device.page_width - tap_w) / 2, year_box.y, tap_w, year_box.h),
        cover.cta_dest,
    )
    specs = Rect(device.writing_clearance, 84.0, device.page_width - 2 * device.writing_clearance, 6.5)
    # ponytail: specs stay fully literal until a dedicated role exists — do not half-apply chrome
    plotter.text(
        specs,
        f"monday weeks  ·  {device.page_width:g} × {device.page_height:g} mm",
        size=8.2,
        face="sans",
        gray=MUTED,
        small_caps=True,
        align="center",
    )


def paint_annual(plotter: Plotter, box: Rect, grid: AnnualGrid, *, body: BodyRamp) -> None:
    for r, band in enumerate(rows(box, 4, gap=2.6)):
        for c, cell in enumerate(columns(band, 3, gap=3.4)):
            _paint_mini_month(plotter, cell, grid.months[r * 3 + c], body=body)


PROJECT_CARD_GAP = 2.6
PROJECT_COL_GAP = 2.8
PROJECT_COL_WEIGHTS = (0.48, 0.52)
PROJECT_INSET_X = 1.8
PROJECT_INSET_Y = 1.5
PROJECT_HEADER_H = 6.2
PROJECT_STATUS_H = 7.4
PROJECT_LEFT_GAP = 1.0
PROJECT_P = 5.0
PROJECT_STATUS_MARK = 3.2


def project_card_seats(well: Rect, cards: int) -> tuple[Rect, ...]:
    """One row track per project card."""
    return rows(well, cards, gap=PROJECT_CARD_GAP)


def project_card_columns(card: Rect) -> tuple[Rect, Rect]:
    """Tasks | notes columns inside a card, after a quiet inset."""
    return columns(
        card.inset(PROJECT_INSET_X, PROJECT_INSET_Y),
        2,
        gap=PROJECT_COL_GAP,
        weights=PROJECT_COL_WEIGHTS,
    )


def project_card_left_seats(left: Rect) -> tuple[Rect, Rect, Rect]:
    """P+name, task ticks, Todo/Doing/Done — stacked in the left column."""
    header, rest = left.split_top(PROJECT_HEADER_H)
    mid = Rect(
        rest.x,
        rest.y + PROJECT_LEFT_GAP,
        rest.w,
        rest.h - PROJECT_LEFT_GAP,
    )
    tasks, status = rows(
        mid,
        2,
        gap=PROJECT_LEFT_GAP,
        weights=(mid.h - PROJECT_STATUS_H - PROJECT_LEFT_GAP, PROJECT_STATUS_H),
    )
    return header, tasks, status


TICKET_GAP = 1.4
TICKET_STUB_W = 12.0
TICKET_INSET_X = 1.6
TICKET_INSET_Y = 1.1
TICKET_MARK = 5.6
TICKET_PERF_DASH = 0.52
TICKET_PERF_GAP = 0.40
TICKET_NAME_WEIGHTS = (0.55, 0.45)
TICKET_BODY_GAP = 1.8
TICKET_PREVIEW_GAP = 1.4
TICKET_PREVIEW_INSET = 0.35
TICKET_STRIP_PAD = 0.40
TICKET_STRIP_LEFT = 0.30
TICKET_STRIP_GRAY = RULE_C

# G (#215) symbol strip — same marks, size, and strip height.
CLONE_ICON = 2.1
CLONE_ICON_GAP = 0.85
CLONE_STRIP_H = 2.8
CLONE_STRIP_COL_GAP = 1.05
CLONE_ICONS = (
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
CLONE_SPINE_W = 1.4
CLONE_RAIL_GAP = 2.6
CLONE_RAIL_WEIGHTS = (0.76, 0.24)
CLONE_CARD_WEIGHTS = (0.50, 0.50)
CLONE_INSET_X = 1.6
CLONE_INSET_Y = 1.4
CLONE_COL_GAP = 3.4
CLONE_STAR = 2.0
CLONE_TRACK_H = 26.0
CLONE_RAIL_SLOT_GAP = 1.8
CLONE_STATUS_LABELS = ("Todo", "In Progress", "Done")
CLONE_P_PAD = 0.40
CLONE_P_CORNER = (2.15, 1.85)
CLONE_NAME_GAP = 1.4
CLONE_TASK_TOP = 0.4
CLONE_TASK_CLEAR = 0.55
CLONE_DOT_PITCH = 2.8
CLONE_DOT = 0.32


def project_ticket_seats(well: Rect, n: int) -> tuple[Rect, ...]:
    """Equal stacked ticket rows filling the well."""
    return rows(well, n, gap=TICKET_GAP)


def project_ticket_parts(ticket: Rect) -> tuple[Rect, Rect]:
    """Stub | title body, after a quiet inset."""
    inner = ticket.inset(TICKET_INSET_X, TICKET_INSET_Y)
    return inner.split_left(TICKET_STUB_W)


def project_ticket_body_seats(body: Rect) -> tuple[Rect, Rect]:
    """Write-in name | three-card preview (~0.45 of the body so boxes read)."""
    return columns(body, 2, gap=TICKET_BODY_GAP, weights=TICKET_NAME_WEIGHTS)


def project_ticket_preview_cards(preview: Rect) -> tuple[Rect, ...]:
    """G's three cards, side-by-side thumbnail — hairline open frames."""
    pocket = preview.inset(TICKET_PREVIEW_INSET, TICKET_PREVIEW_INSET)
    return columns(pocket, 3, gap=TICKET_PREVIEW_GAP)


def project_ticket_name_seats(name: Rect) -> tuple[Rect, Rect]:
    """Write-in band over G's 9-mark strip. Hline sits at the band bottom."""
    block = CLONE_STRIP_H + TICKET_STRIP_PAD
    write_h = max(name.h - block, 1)
    write = Rect(name.x, name.y, name.w, write_h)
    strip = Rect(
        name.x + TICKET_STRIP_LEFT,
        write.bottom + TICKET_STRIP_PAD,
        name.w - TICKET_STRIP_LEFT,
        CLONE_STRIP_H,
    )
    return write, strip


def project_ticket_link_hits(ticket: Rect) -> tuple[Rect, ...]:
    """Stub column + each preview card. Write-in and symbol strip stay unlinkable."""
    stub, body = project_ticket_parts(ticket)
    _, preview = project_ticket_body_seats(body)
    return (stub, *project_ticket_preview_cards(preview))


def paint_projects_index(plotter: Plotter, box: Rect, index: ProjectsIndex, *, body: BodyRamp) -> None:
    """Thesis L — stub, raised write-in, G symbol strip, 3-card preview; stub + preview links."""
    for seat, ticket in zip(project_ticket_seats(box, len(index.tickets)), index.tickets, strict=True):
        _paint_project_ticket(plotter, seat, ticket, body=body)
        for hit in project_ticket_link_hits(seat):
            plotter.link(hit, ticket.dest)


def _paint_project_ticket(
    plotter: Plotter, box: Rect, ticket: ProjectTicket, *, body: BodyRamp
) -> None:
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    stub, ticket_body = project_ticket_parts(box)
    name, preview = project_ticket_body_seats(ticket_body)
    write, strip = project_ticket_name_seats(name)
    mark_y = stub.y + (stub.h - TICKET_MARK) / 2
    mark = Rect(stub.x + (stub.w - TICKET_MARK) / 2, mark_y, TICKET_MARK, TICKET_MARK)
    plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    _ink_text(
        plotter,
        mark,
        f"{ticket.number:02d}",
        body.ink("strong"),
        align="center",
    )
    perf_x = stub.right + 0.55
    _paint_perforation(plotter, perf_x, box.y + 0.9, perf_x, box.bottom - 0.9)
    plotter.line(write.x, write.bottom, write.right, write.bottom, stroke_width=RULE, stroke_gray=RULE_C)
    _paint_clone_icon_strip(plotter, strip)
    for card in project_ticket_preview_cards(preview):
        plotter.rect(card, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    _paint_perforation(plotter, box.x + 1.4, box.bottom, box.right - 1.4, box.bottom)


def _paint_perforation(
    plotter: Plotter,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    dash: float = TICKET_PERF_DASH,
    gap: float = TICKET_PERF_GAP,
) -> None:
    """Thin dashed hairline — ticket tear, not a solid rule."""
    dx = x2 - x1
    dy = y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 0:
        return
    ux, uy = dx / length, dy / length
    walked = 0.0
    while walked < length:
        start = walked
        stop = min(walked + dash, length)
        plotter.line(
            x1 + ux * start,
            y1 + uy * start,
            x1 + ux * stop,
            y1 + uy * stop,
            stroke_width=HAIR,
            stroke_gray=INK,
        )
        walked = stop + gap


def clone_icon_cluster_width(n: int = len(CLONE_ICONS)) -> float:
    """Minimum packed width of the G icon set (spread uses the full strip seat)."""
    return n * CLONE_ICON + max(n - 1, 0) * CLONE_ICON_GAP


def clone_task_count(box: Rect) -> int:
    """Focus rows that fill ``box``, with clearance above the symbol strip."""
    usable = box.h - CLONE_TASK_TOP - CLONE_TASK_CLEAR
    if usable < TICK:
        return 1
    return max(1, int((usable - TICK) / FOCUS_PITCH) + 1)


def projects_clone_a_name_field(header: Rect) -> tuple[Rect, Rect]:
    """P square and the bordered name field beside it."""
    y = header.y + (header.h - PROJECT_P) / 2
    mark = Rect(header.x, y, PROJECT_P, PROJECT_P)
    field = Rect(
        mark.right + CLONE_NAME_GAP,
        y,
        max(header.right - mark.right - CLONE_NAME_GAP, 1),
        PROJECT_P,
    )
    return mark, field


def projects_clone_a_well(well: Rect) -> tuple[Rect, Rect]:
    """Board column | status rail — kanban’s right-hand track, Nomad-narrow."""
    return columns(well, 2, gap=CLONE_RAIL_GAP, weights=CLONE_RAIL_WEIGHTS)


def projects_clone_a_seats(well: Rect, cards: int) -> tuple[tuple[Rect, ...], tuple[Rect, ...]]:
    """Stacked project cards and the matching three-stage rail seats."""
    board, rail = projects_clone_a_well(well)
    return project_card_seats(board, cards), rows(rail, cards, gap=PROJECT_CARD_GAP)


def projects_clone_a_card(card: Rect) -> tuple[Rect, Rect, Rect, Rect, Rect, Rect]:
    """spine, header, name field, tasks, notes (full right), icon strip (left)."""
    spine = Rect(card.x, card.y, CLONE_SPINE_W, card.h)
    body = Rect(card.x + CLONE_SPINE_W, card.y, card.w - CLONE_SPINE_W, card.h).inset(
        CLONE_INSET_X, CLONE_INSET_Y
    )
    left, notes = columns(body, 2, gap=CLONE_COL_GAP, weights=CLONE_CARD_WEIGHTS)
    name_h, left_rest = left.split_top(PROJECT_HEADER_H)
    _, name_field = projects_clone_a_name_field(name_h)
    mid = Rect(
        left_rest.x,
        left_rest.y + PROJECT_LEFT_GAP,
        left_rest.w,
        left_rest.h - PROJECT_LEFT_GAP,
    )
    tasks, strip = rows(
        mid,
        2,
        gap=PROJECT_LEFT_GAP,
        weights=(mid.h - CLONE_STRIP_H - PROJECT_LEFT_GAP, CLONE_STRIP_H),
    )
    return spine, name_h, name_field, tasks, notes, strip


def paint_project(plotter: Plotter, box: Rect, board: ProjectsBoard, *, body: BodyRamp) -> None:
    """G #215 clone well — spine, soft P + name box, ticks, 2.8 mm dots, strip, status rail."""
    cards, rails = projects_clone_a_seats(box, board.cards)
    _wash(plotter, projects_clone_a_well(box)[1], WASH)
    for card, rail in zip(cards, rails, strict=True):
        spine, name_h, name_field, tasks, notes, strip = projects_clone_a_card(card)
        plotter.rect(spine, stroke=False, fill=True, fill_gray=INK)
        _paint_clone_priority(plotter, name_h, body=body)
        plotter.rect(name_field, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
        _paint_clone_tasks(plotter, tasks)
        _paint_clone_dot_grid(plotter, notes)
        _paint_clone_icon_strip(plotter, strip)
        _paint_clone_status_track(plotter, rail, body=body)
        plotter.rect(card, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)


def _paint_clone_dot_grid(plotter: Plotter, box: Rect) -> None:
    """E-ink dot grid — SOFT pocket, RULE_C dots on tracks at note pitch."""
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    inset = Rect(box.x + 1.1, box.y + 1.2, box.w - 2.2, box.h - 2.4)
    nx = max(2, int(inset.w / CLONE_DOT_PITCH))
    ny = max(2, int(inset.h / CLONE_DOT_PITCH))
    for band in rows(inset, ny):
        for cell in columns(band, nx):
            plotter.rect(
                Rect(
                    cell.x + (cell.w - CLONE_DOT) / 2,
                    cell.y + (cell.h - CLONE_DOT) / 2,
                    CLONE_DOT,
                    CLONE_DOT,
                ),
                stroke=False,
                fill=True,
                fill_gray=RULE_C,
            )


def _paint_clone_priority(plotter: Plotter, header: Rect, *, body: BodyRamp) -> float:
    """P-box: muted corner-fraction label, leftover is write-in. Clone only."""
    mark, _field = projects_clone_a_name_field(header)
    plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    cw, ch = CLONE_P_CORNER
    _ink_text(
        plotter,
        Rect(mark.x + CLONE_P_PAD, mark.y + CLONE_P_PAD, cw, ch),
        "P",
        body.ink("caption"),
        gray=MUTED,
        small_caps=True,
    )
    return mark.bottom


def _paint_clone_tasks(plotter: Plotter, box: Rect, n: int | None = None) -> None:
    count = clone_task_count(box) if n is None else max(1, n)
    y = box.y + CLONE_TASK_TOP
    star_right = box.right - CLONE_STAR - 1.0
    for _ in range(count):
        _paint_focus_row(plotter, box.x, y, star_right)
        star = Rect(
            box.right - CLONE_STAR,
            y + (TICK - CLONE_STAR) / 2,
            CLONE_STAR,
            CLONE_STAR,
        )
        _paint_diamond(plotter, star)
        y += FOCUS_PITCH


def _paint_clone_status_track(plotter: Plotter, box: Rect, *, body: BodyRamp) -> None:
    """Vertical Todo → In Progress → Done. Squares stand in for circles."""
    track_h = min(CLONE_TRACK_H, box.h - 2.0)
    track = Rect(box.x, box.y + (box.h - track_h) / 2, box.w, track_h)
    inset = track.inset(1.4, 0.6)
    marks: list[Rect] = []
    caption = body.ink("caption")
    for slot, label in zip(rows(inset, 3, gap=CLONE_RAIL_SLOT_GAP), CLONE_STATUS_LABELS, strict=True):
        mark_y = slot.y + (slot.h - PROJECT_STATUS_MARK) / 2
        mark = Rect(slot.x, mark_y, PROJECT_STATUS_MARK, PROJECT_STATUS_MARK)
        plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
        _ink_text(
            plotter,
            Rect(mark.right + 0.7, slot.y, max(slot.right - mark.right - 0.7, 1), slot.h),
            label,
            caption,
            gray=MUTED,
            small_caps=True,
        )
        marks.append(mark)
    cx = marks[0].x + marks[0].w / 2
    for above, below in zip(marks, marks[1:]):
        plotter.line(cx, above.bottom, cx, below.y, stroke_width=HAIR, stroke_gray=INK)


def _paint_diamond(plotter: Plotter, box: Rect) -> None:
    """Hairline rhombus — favorite/tag stand-in where ★ is missing."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    plotter.line(cx, box.y, box.right, cy, stroke_width=HAIR, stroke_gray=INK)
    plotter.line(box.right, cy, cx, box.bottom, stroke_width=HAIR, stroke_gray=INK)
    plotter.line(cx, box.bottom, box.x, cy, stroke_width=HAIR, stroke_gray=INK)
    plotter.line(box.x, cy, cx, box.y, stroke_width=HAIR, stroke_gray=INK)


def _paint_clone_icon_strip(plotter: Plotter, box: Rect) -> None:
    """Filled icons, even spread — same craft as G's project-card strip."""
    slots = columns(box, len(CLONE_ICONS), gap=CLONE_STRIP_COL_GAP)
    for slot, kind in zip(slots, CLONE_ICONS, strict=True):
        s = min(CLONE_ICON, slot.h - 0.2, slot.w)
        icon = Rect(slot.x + (slot.w - s) / 2, slot.y + (slot.h - s) / 2, s, s)
        _paint_clone_icon(plotter, icon, kind)


def _paint_clone_icon(plotter: Plotter, box: Rect, kind: str) -> None:
    match kind:
        case "square":
            plotter.rect(box, stroke=False, fill=True, fill_gray=TICKET_STRIP_GRAY)
        case "plus":
            arm = 0.30
            plotter.rect(
                Rect(box.x + box.w * (1 - arm) / 2, box.y, box.w * arm, box.h),
                stroke=False,
                fill=True,
                fill_gray=TICKET_STRIP_GRAY,
            )
            plotter.rect(
                Rect(box.x, box.y + box.h * (1 - arm) / 2, box.w, box.h * arm),
                stroke=False,
                fill=True,
                fill_gray=TICKET_STRIP_GRAY,
            )
        case "circle":
            _fill_circle(plotter, box)
        case "diamond":
            _fill_diamond(plotter, box)
        case "triangle":
            _fill_triangle(plotter, box)
        case "crescent":
            _fill_crescent(plotter, box)
        case "hexagon":
            _fill_hexagon(plotter, box)
        case "cross":
            _fill_cross(plotter, box)
        case "star":
            _fill_star(plotter, box)
        case _:
            raise ValueError(f"unknown clone icon {kind!r}")


def _scan_box(box: Rect, *, n: int = 11) -> tuple[list[float], float]:
    dy = box.h / n
    return [box.y + (i + 0.5) * dy for i in range(n)], dy


def _fill_circle(plotter: Plotter, box: Rect) -> None:
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    rx = box.w / 2
    ry = box.h / 2
    ys, dy = _scan_box(box)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        t = (y - cy) / ry
        if abs(t) >= 1:
            continue
        half = rx * math.sqrt(max(0.0, 1.0 - t * t))
        spans.append((y - dy / 2, cx - half, cx + half))
    _fill_span_rows(plotter, spans, dy)


def _fill_diamond(plotter: Plotter, box: Rect) -> None:
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    rx = box.w / 2
    ry = box.h / 2
    ys, dy = _scan_box(box)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        t = abs((y - cy) / ry)
        if t >= 1:
            continue
        half = rx * (1.0 - t)
        spans.append((y - dy / 2, cx - half, cx + half))
    _fill_span_rows(plotter, spans, dy)


def _fill_triangle(plotter: Plotter, box: Rect) -> None:
    """Point-up triangle inscribed in ``box``."""
    ys, dy = _scan_box(box)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        t = (y - box.y) / box.h
        half = (box.w / 2) * t
        cx = box.x + box.w / 2
        spans.append((y - dy / 2, cx - half, cx + half))
    _fill_span_rows(plotter, spans, dy)


def _fill_poly(plotter: Plotter, box: Rect, pts: list[tuple[float, float]], *, n: int = 12) -> None:
    ys, dy = _scan_box(box, n=n)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        xs = _poly_xs_at(pts, y)
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            spans.append((y - dy / 2, xs[i], xs[i + 1]))
    _fill_span_rows(plotter, spans, dy)


def _fill_crescent(plotter: Plotter, box: Rect) -> None:
    """Waxing crescent — outer disc minus an offset disc. Distinct from circle."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    rx = box.w / 2
    ry = box.h / 2
    ox = cx + rx * 0.36
    r2x = rx * 0.78
    r2y = ry * 0.78
    ys, dy = _scan_box(box, n=13)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        t = (y - cy) / ry
        if abs(t) >= 1:
            continue
        half = rx * math.sqrt(max(0.0, 1.0 - t * t))
        left, right = cx - half, cx + half
        t2 = (y - cy) / r2y
        if abs(t2) < 1:
            cut = r2x * math.sqrt(max(0.0, 1.0 - t2 * t2))
            cut_l, cut_r = ox - cut, ox + cut
            if cut_l <= left < cut_r < right:
                left = cut_r
            elif left < cut_l < right <= cut_r:
                right = cut_l
            elif cut_l <= left and right <= cut_r:
                continue
        if right - left > 0.08:
            spans.append((y - dy / 2, left, right))
    _fill_span_rows(plotter, spans, dy)


def _fill_hexagon(plotter: Plotter, box: Rect) -> None:
    """Pointy-top hexagon — distinct from square and diamond."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    r = min(box.w, box.h) / 2
    pts = [
        (cx + r * math.cos(math.radians(-90 + i * 60)), cy + r * math.sin(math.radians(-90 + i * 60)))
        for i in range(6)
    ]
    _fill_poly(plotter, box, pts)


def _fill_cross(plotter: Plotter, box: Rect) -> None:
    """X — two thick diagonals. Distinct from plus and from the 5-point star."""
    t = min(box.w, box.h) * 0.22
    x0, y0, x1, y1 = box.x, box.y, box.right, box.bottom
    _fill_poly(plotter, box, [(x0 + t, y0), (x1, y1 - t), (x1 - t, y1), (x0, y0 + t)])
    _fill_poly(plotter, box, [(x1 - t, y0), (x1, y0 + t), (x0 + t, y1), (x0, y1 - t)])


def _fill_star(plotter: Plotter, box: Rect) -> None:
    """Five-point star — same as G."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    r = min(box.w, box.h) / 2
    _fill_poly(plotter, box, _star_poly(cx, cy, r), n=13)


def _star_poly(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    r_in = r * 0.38
    pts: list[tuple[float, float]] = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rad = r if i % 2 == 0 else r_in
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pts


def _poly_xs_at(pts: list[tuple[float, float]], y: float) -> list[float]:
    xs: list[float] = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            if y1 != y0:
                xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    return xs


def _fill_span_rows(plotter: Plotter, spans: list[tuple[float, float, float]], dy: float) -> None:
    for y, x0, x1 in spans:
        if x1 - x0 > 0.08:
            plotter.rect(Rect(x0, y, x1 - x0, dy), stroke=False, fill=True, fill_gray=TICKET_STRIP_GRAY)


MEET_GAP = 2.6
MEET_HEAD_INSET_X = 1.8
MEET_HEAD_INSET_Y = 1.2
MEET_HEAD_LINE_H = 5.4
MEET_HEAD_COL_GAP = 2.8
MEET_HEAD_WEIGHTS = (0.64, 0.36)
MEET_LABEL_W = 12.0
MEET_WRITE_LABEL_H = 3.8

MEET_INDEX_GAP = 1.0
MEET_INDEX_INSET_X = 1.2
MEET_INDEX_INSET_Y = 0.7
MEET_INDEX_STUB_W = 9.6
MEET_INDEX_STUB_GAP = 1.6
MEET_INDEX_MARK = 5.0
MEET_INDEX_COL_GAP = 2.8
MEET_INDEX_WEIGHTS = (0.22, 0.78)
MEET_INDEX_DATE_LABEL_W = 8.0


def meeting_head_height() -> float:
    """One-line title|date band — not two stacked write-ins."""
    return MEET_HEAD_INSET_Y * 2 + MEET_HEAD_LINE_H


def _below(box: Rect, gap: float) -> Rect:
    return Rect(box.x, box.y + gap, box.w, box.h - gap)


def meeting_seats(
    well: Rect, agenda: int, action_items: int
) -> tuple[Rect, Rect, Rect, Rect]:
    """Head, agenda, leftover notes, action items. Notes flex."""
    head, rest = well.split_top(meeting_head_height())
    leftover = _below(rest, MEET_GAP)
    agenda_h = checklist_content_height(agenda)
    agenda_box, rest = leftover.split_top(agenda_h)
    leftover = _below(rest, MEET_GAP)
    action_h = checklist_content_height(action_items)
    notes_h = max(leftover.h - action_h - MEET_GAP, 1)
    notes, action_box = rows(leftover, 2, gap=MEET_GAP, weights=(notes_h, action_h))
    return head, agenda_box, notes, action_box


def meeting_head_seats(head: Rect) -> tuple[Rect, Rect]:
    """Title write-in | Date write-in on one horizontal row."""
    inner = head.inset(MEET_HEAD_INSET_X, MEET_HEAD_INSET_Y)
    return columns(inner, 2, gap=MEET_HEAD_COL_GAP, weights=MEET_HEAD_WEIGHTS)


def paint_meeting(plotter: Plotter, box: Rect, agenda: MeetingAgenda, *, body: BodyRamp) -> None:
    """Locked Meeting dest — title|date, agenda, notes, action items."""
    head, agenda_box, notes, action_items = meeting_seats(
        box, agenda.agenda, agenda.action_items
    )
    _paint_meeting_head(plotter, head, body=body)
    _paint_checklist_box(plotter, agenda_box, body=body, label="Agenda", rows=agenda.agenda)
    _paint_note_box(plotter, notes, body=body, label="Notes")
    _paint_checklist_box(
        plotter, action_items, body=body, label="Action items", rows=agenda.action_items
    )


def _paint_meeting_head(plotter: Plotter, head: Rect, *, body: BodyRamp) -> None:
    plotter.rect(head, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    title, dated = meeting_head_seats(head)
    _paint_meeting_writein(plotter, title, "Title", body=body)
    _paint_meeting_writein(plotter, dated, "Date", body=body)


def _paint_meeting_writein(plotter: Plotter, box: Rect, label: str, *, body: BodyRamp) -> None:
    """Label and underline share a baseline — rule sits just under the scaps."""
    tag, write = box.split_left(MEET_LABEL_W)
    rule_y = box.bottom
    label_box = Rect(tag.x, rule_y - MEET_WRITE_LABEL_H, tag.w, MEET_WRITE_LABEL_H)
    _ink_text(plotter, label_box, label, body.ink("label"), gray=MUTED, small_caps=True)
    plotter.line(write.x, rule_y, write.right, rule_y, stroke_width=RULE, stroke_gray=RULE_C)


def meetings_index_roster(box: Rect, n: int) -> tuple[Rect, ...]:
    """Equal stacked roster rows filling the well."""
    return rows(box, n, gap=MEET_INDEX_GAP)


def meeting_index_row_parts(row: Rect) -> tuple[Rect, Rect]:
    """Stub | date+title body, after a quiet inset and stub gap."""
    inner = row.inset(MEET_INDEX_INSET_X, MEET_INDEX_INSET_Y)
    stub, rest = inner.split_left(MEET_INDEX_STUB_W)
    body = Rect(rest.x + MEET_INDEX_STUB_GAP, rest.y, rest.w - MEET_INDEX_STUB_GAP, rest.h)
    return stub, body


def meeting_index_row_seats(row: Rect) -> tuple[Rect, Rect]:
    """Date cue | title write-in on the body. Stub is not a write-in."""
    _, body = meeting_index_row_parts(row)
    return columns(body, 2, gap=MEET_INDEX_COL_GAP, weights=MEET_INDEX_WEIGHTS)


def meeting_index_link_hits(row: Rect) -> tuple[Rect, ...]:
    """Stub column only. Date and title write-ins stay unlinkable."""
    stub, _body = meeting_index_row_parts(row)
    return (stub,)


def paint_meetings_index(plotter: Plotter, box: Rect, index: MeetingIndex, *, body: BodyRamp) -> None:
    """Thesis A — dense dated roster. Stub is the dest hit; write-ins stay unlinkable."""
    for seat, slot in zip(meetings_index_roster(box, len(index.slots)), index.slots, strict=True):
        _paint_meeting_index_row(plotter, seat, slot.number, body=body)
        for hit in meeting_index_link_hits(seat):
            plotter.link(hit, slot.dest)


def _paint_meeting_index_row(plotter: Plotter, box: Rect, number: int, *, body: BodyRamp) -> None:
    """Slot stub + date cue + title write-in/rule on one baseline."""
    stub, _ticket_body = meeting_index_row_parts(box)
    _paint_meeting_index_stub(plotter, stub, number, body=body)
    dated, title = meeting_index_row_seats(box)
    _paint_meeting_index_date_cue(plotter, dated, body=body)
    _paint_meeting_index_title(plotter, title)


def _paint_meeting_index_stub(plotter: Plotter, stub: Rect, number: int, *, body: BodyRamp) -> None:
    """Hairline slot mark — the visible tap target, Projects L spirit."""
    mark_y = stub.y + (stub.h - MEET_INDEX_MARK) / 2
    mark = Rect(stub.x + (stub.w - MEET_INDEX_MARK) / 2, mark_y, MEET_INDEX_MARK, MEET_INDEX_MARK)
    plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    _ink_text(plotter, mark, f"{number:02d}", body.ink("strong"), align="center")


def _paint_meeting_index_date_cue(plotter: Plotter, box: Rect, *, body: BodyRamp) -> None:
    """Muted Date label + short write-in — the date cue, not a printed calendar."""
    tag, write = box.split_left(MEET_INDEX_DATE_LABEL_W)
    rule_y = box.bottom
    _ink_text(
        plotter,
        Rect(tag.x, rule_y - MEET_WRITE_LABEL_H, tag.w, MEET_WRITE_LABEL_H),
        "Date",
        body.ink("caption"),
        gray=MUTED,
        small_caps=True,
    )
    plotter.line(write.x, rule_y, write.right, rule_y, stroke_width=RULE, stroke_gray=RULE_C)


def _paint_meeting_index_title(plotter: Plotter, box: Rect) -> None:
    """Title write-in rule on the same baseline as the date cue."""
    plotter.line(box.x, box.bottom, box.right, box.bottom, stroke_width=RULE, stroke_gray=RULE_C)


TASK_INDEX_BAND_GAP = 2.6
TASK_INDEX_INSET_X = 1.8
TASK_INDEX_INSET_Y = 1.4
TASK_INDEX_HEAD_H = 4.2
TASK_INDEX_HEAD_GAP = 0.8
TASK_INDEX_ROW_GAP = 1.0
TASK_INDEX_LINE_H = 5.4
TASK_INDEX_WEEK_W = 12.0
# Midpoint of original fat column (26) and hug (14.8).
TASK_INDEX_RANGE_W = 20.4
# Midpoint of original WRITE_GAP (2.8) and 4pt (1.41).
TASK_INDEX_WRITE_GAP = 2.105
TASK_GAP = 2.6
TASK_CHECKLIST_FRAC = 2 / 3


def tasks_index_bands(well: Rect, week_counts: tuple[int, ...]) -> tuple[Rect, ...]:
    """Month bands weighted by week-row count. Horizon scan, not equal status slices."""
    weights = tuple(float(max(1, count)) for count in week_counts)
    return rows(well, len(weights), gap=TASK_INDEX_BAND_GAP, weights=weights)


def tasks_index_band_seats(band: Rect, n: int) -> tuple[Rect, tuple[Rect, ...]]:
    """Month header over linked week rows, after a quiet inset."""
    inner = band.inset(TASK_INDEX_INSET_X, TASK_INDEX_INSET_Y)
    head, rest = inner.split_top(TASK_INDEX_HEAD_H)
    body = Rect(rest.x, rest.y + TASK_INDEX_HEAD_GAP, rest.w, rest.h - TASK_INDEX_HEAD_GAP)
    return head, rows(body, n, gap=TASK_INDEX_ROW_GAP)


def tasks_index_week_strip(row: Rect) -> Rect:
    """Content-height text+rule strip, vertically centered in the stretched week row."""
    h = min(TASK_INDEX_LINE_H, row.h)
    return Rect(row.x, row.y + (row.h - h) / 2, row.w, h)


def tasks_index_rule_y(row: Rect) -> float:
    """Write-in baseline — strip bottom, not the stretched row floor."""
    return tasks_index_week_strip(row).bottom


def tasks_index_week_parts(row: Rect) -> tuple[Rect, Rect, Rect]:
    """Wnn stub | printed range | write-in — ``tracks.columns``; gap only date→hline."""
    strip = tasks_index_week_strip(row)
    stub_w = TASK_INDEX_WEEK_W
    stub, rest = columns(strip, 2, gap=0, weights=(stub_w, max(strip.w - stub_w, 1)))
    range_w = TASK_INDEX_RANGE_W
    write_w = max(rest.w - TASK_INDEX_WRITE_GAP - range_w, 1)
    dated, write = columns(rest, 2, gap=TASK_INDEX_WRITE_GAP, weights=(range_w, write_w))
    return stub, dated, write


def tasks_index_link_hits(row: Rect) -> tuple[Rect, ...]:
    """Stub + week range. Write-in hline stays unlinkable (Meeting A / Projects L)."""
    stub, dated, _write = tasks_index_week_parts(row)
    return (stub, dated)


def paint_tasks_index(plotter: Plotter, box: Rect, index: TasksIndex, *, body: BodyRamp) -> None:
    """Thesis C — month-banded week rows. Not Active/Waiting/Done, not This week/Later."""
    counts = tuple(len(band.weeks) for band in index.bands)
    for band_box, band in zip(tasks_index_bands(box, counts), index.bands, strict=True):
        plotter.rect(band_box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
        head, lines = tasks_index_band_seats(band_box, len(band.weeks))
        _ink_text(
            plotter,
            head,
            band.name,
            body.ink("label"),
            small_caps=True,
            weight="bold",
        )
        plotter.line(head.x, head.bottom, head.right, head.bottom, stroke_width=HAIR, stroke_gray=SOFT)
        for line, week in zip(lines, band.weeks, strict=True):
            _paint_tasks_index_week(plotter, line, week, body=body)
            for hit in tasks_index_link_hits(line):
                plotter.link(hit, week.dest)


def _paint_tasks_index_week(plotter: Plotter, row: Rect, week: TaskWeek, *, body: BodyRamp) -> None:
    stub, dated, write = tasks_index_week_parts(row)
    _ink_text(plotter, stub, f"W{week.iso_week:02d}", body.ink("strong"))
    _ink_text(
        plotter,
        dated,
        short_date_range(week.monday, week.sunday),
        body.ink("caption"),
        gray=MUTED,
        small_caps=True,
    )
    rule_y = tasks_index_rule_y(row)
    plotter.line(
        write.x,
        rule_y,
        write.right,
        rule_y,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )


def task_row_count(well: Rect, floor: int = 1) -> int:
    """Tick rows that fill ≈⅔ of the well (minus ``TASK_GAP``), unlabeled."""
    target = (well.h - TASK_GAP) * TASK_CHECKLIST_FRAC
    usable = target - FOCUS_PAD_TOP - FOCUS_PAD_BOT
    if usable < TICK:
        fitted = 1
    else:
        fitted = max(1, int((usable - TICK) / FOCUS_PITCH) + 1)
    return max(floor, fitted)


def task_seats(well: Rect, rows_n: int | None = None) -> tuple[Rect, Rect]:
    """Unlabeled checklist ≈⅔ of well (minus ``TASK_GAP``); Notes take the leftover."""
    n = task_row_count(well) if rows_n is None else rows_n
    check, rest = well.split_top(checklist_content_height(n, labeled=False))
    notes = Rect(rest.x, rest.y + TASK_GAP, rest.w, rest.h - TASK_GAP)
    return check, notes


def paint_task(plotter: Plotter, box: Rect, page: TasksWeekPage, *, body: BodyRamp) -> None:
    """Weekly Tasks dest — unlabeled ⅔ checklist + leftover notes. Chip is the week."""
    rows_n = task_row_count(box, floor=page.rows)
    checklist, notes = task_seats(box, rows_n)
    _paint_checklist_box(plotter, checklist, body=body, rows=rows_n)
    _paint_note_box(plotter, notes, body=body, label="Notes")


REVIEW_INDEX_BAND_GAP = 1.6
REVIEW_INDEX_MONTH_W = 20.0
REVIEW_INDEX_LABEL_GAP = 1.6
REVIEW_INDEX_CHIP_GAP = 1.2
REVIEW_INDEX_CHIP_INSET_X = 0.35
REVIEW_INDEX_CHIP_H = 6.8
REVIEW_GAP = 2.6
REVIEW_DAY_GAP = 1.0
REVIEW_STRIP_H = 18.0
REVIEW_DAY_INSET_X = 0.7
REVIEW_DAY_INSET_Y = 0.55
REVIEW_DOW_H = 3.6
REVIEW_NUM_H = 5.4


def review_index_cols(week_counts: tuple[int, ...]) -> int:
    """Shared chip-column count so month rows align across the grid."""
    return max((max(1, count) for count in week_counts), default=1)


def review_index_month_rows(well: Rect, n: int) -> tuple[Rect, ...]:
    """Equal-height month rows. Hairlines read across; weeks are the chips."""
    return rows(well, n, gap=REVIEW_INDEX_BAND_GAP)


def review_index_row_parts(
    row: Rect, n_weeks: int, n_cols: int
) -> tuple[Rect, tuple[Rect, ...]]:
    """Month stub | aligned week-chip columns — ``tracks.columns``."""
    stub_w = REVIEW_INDEX_MONTH_W
    grid_w = max(row.w - stub_w - REVIEW_INDEX_LABEL_GAP, 1)
    stub, grid = columns(row, 2, gap=REVIEW_INDEX_LABEL_GAP, weights=(stub_w, grid_w))
    cells = columns(grid, n_cols, gap=REVIEW_INDEX_CHIP_GAP)
    return stub, cells[:n_weeks]


def review_index_chip(cell: Rect) -> Rect:
    """Content-height chip, vertically centered — dense cell, not a stretched box."""
    h = min(REVIEW_INDEX_CHIP_H, cell.h)
    return Rect(
        cell.x + REVIEW_INDEX_CHIP_INSET_X,
        cell.y + (cell.h - h) / 2,
        max(cell.w - 2 * REVIEW_INDEX_CHIP_INSET_X, 1),
        h,
    )


def review_index_link_hits(cell: Rect) -> tuple[Rect, ...]:
    """Whole chip is the dest hit — no write-in on the dense grid."""
    return (review_index_chip(cell),)


def review_index_rule_y(row: Rect) -> float:
    """Month hairline — row floor, spanning the well so months read across."""
    return row.bottom


def paint_review_index(plotter: Plotter, box: Rect, index: ReviewIndex, *, body: BodyRamp) -> None:
    """Thesis B — dense week chips in several columns; month headers + hairlines."""
    counts = tuple(len(band.weeks) for band in index.bands)
    n_cols = review_index_cols(counts)
    bands = review_index_month_rows(box, len(index.bands))
    for i, (row, band) in enumerate(zip(bands, index.bands, strict=True)):
        stub, cells = review_index_row_parts(row, len(band.weeks), n_cols)
        _ink_text(
            plotter,
            stub,
            band.name,
            body.ink("label"),
            small_caps=True,
            weight="bold",
        )
        for cell, week in zip(cells, band.weeks, strict=True):
            _paint_review_index_chip(plotter, cell, week, body=body)
            for hit in review_index_link_hits(cell):
                plotter.link(hit, week.dest)
        if i + 1 < len(bands):
            rule_y = review_index_rule_y(row)
            plotter.line(
                box.x,
                rule_y,
                box.right,
                rule_y,
                stroke_width=HAIR,
                stroke_gray=SOFT,
            )


def _paint_review_index_chip(
    plotter: Plotter, cell: Rect, week: ReviewWeek, *, body: BodyRamp
) -> None:
    chip = review_index_chip(cell)
    plotter.rect(chip, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    _ink_text(plotter, chip, f"W{week.iso_week:02d}", body.ink("strong"), align="center")


def review_seats(well: Rect) -> tuple[Rect, Rect]:
    """Mon–Sun cue strip over leftover week narrative. Strip is content-height; notes flex."""
    strip, rest = well.split_top(REVIEW_STRIP_H)
    notes = Rect(rest.x, rest.y + REVIEW_GAP, rest.w, rest.h - REVIEW_GAP)
    return strip, notes


def review_day_cues(strip: Rect) -> tuple[Rect, ...]:
    """Seven equal day columns — ``tracks.columns``. Horizon scan, not status slices."""
    return columns(strip, 7, gap=REVIEW_DAY_GAP)


def review_day_parts(cue: Rect) -> tuple[Rect, Rect]:
    """Dow+date label | one-line write-in. ``tracks`` after a quiet inset."""
    inner = cue.inset(REVIEW_DAY_INSET_X, REVIEW_DAY_INSET_Y)
    label_h = REVIEW_DOW_H + REVIEW_NUM_H
    return inner.split_top(label_h)


def review_day_link_hits(cue: Rect) -> tuple[Rect, ...]:
    """Label only. Write-in stays unlinkable (Meeting A / Tasks C)."""
    label, _write = review_day_parts(cue)
    return (label,)


def review_day_rule_y(cue: Rect) -> float:
    """One-line prompt baseline — mid write pocket, not the hairline box floor."""
    _label, write = review_day_parts(cue)
    return write.y + min(4.15, write.h * 0.55)


def paint_review(plotter: Plotter, box: Rect, page: ReviewWeekPage, *, body: BodyRamp) -> None:
    """Thesis E — seven day cues, then unlabeled week narrative. Chrome names the page."""
    strip, notes = review_seats(box)
    for cue, day in zip(review_day_cues(strip), page.days, strict=True):
        _paint_review_day_cue(plotter, cue, day, body=body)
        if day.dest:
            for hit in review_day_link_hits(cue):
                plotter.link(hit, day.dest)
    _paint_note_box(plotter, notes, body=body)


def _paint_review_day_cue(plotter: Plotter, cue: Rect, day: ReviewDay, *, body: BodyRamp) -> None:
    """Mini write: weekday + date over a one-line prompt. Hairline pocket."""
    plotter.rect(cue, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    label, write = review_day_parts(cue)
    ink = INK if day.dest else MUTED
    dow = Rect(label.x, label.y, label.w, REVIEW_DOW_H)
    num = Rect(label.x, dow.bottom, label.w, REVIEW_NUM_H)
    _ink_text(
        plotter,
        dow,
        day.weekday_label,
        body.ink("caption"),
        gray=MUTED,
        small_caps=True,
        align="center",
    )
    _ink_text(
        plotter,
        num,
        str(day.day.day),
        body.ink("calendar_num"),
        gray=ink,
        align="center",
    )
    rule_y = review_day_rule_y(cue)
    plotter.line(
        write.x,
        rule_y,
        write.right,
        rule_y,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )


def paint_quarter(plotter: Plotter, box: Rect, grid: QuarterGrid, *, body: BodyRamp) -> None:
    """Default quarter seat is A″ — year-density minis, content-height Focus over flex Notes."""
    paint_quarter_a_focus_notes(plotter, box, grid, body=body)


def quarter_seats_a_shortband(box: Rect) -> tuple[Rect, Rect, Rect]:
    """Older A: top band ≈ well.h/4, three mini-months, leftover empty."""
    band = rows(box, 4)[0]
    jan, feb, mar = columns(band, 3, gap=4.0)
    return jan, feb, mar


def quarter_seats_a_note_boxes(box: Rect) -> tuple[tuple[Rect, Rect], ...]:
    """A′: three columns; each is (compact mini-month, leftover note box)."""
    cal_h = rows(box, 4, gap=2.6)[0].h
    gap = 2.6
    seats: list[tuple[Rect, Rect]] = []
    for col in columns(box, 3, gap=4.0):
        cal, rest = col.split_top(cal_h)
        notes = Rect(rest.x, rest.y + gap, rest.w, rest.h - gap)
        seats.append((cal, notes))
    return tuple(seats)


def quarter_seats_b_stack(box: Rect) -> tuple[Rect, Rect, Rect]:
    """Comparison B: top Jan|Feb, bottom Mar at the same cell width, left-aligned."""
    top, bottom = rows(box, 2, gap=4.0)
    jan, feb = columns(top, 2, gap=4.0)
    mar = Rect(bottom.x, bottom.y, jan.w, bottom.h)
    return jan, feb, mar


def quarter_seats_c_stack_notes(box: Rect) -> tuple[tuple[Rect, Rect, Rect], Rect]:
    """Comparison C: left stacked minis, right shared notes well."""
    left, right = columns(box, 2, gap=3.4, weights=(0.4, 0.6))
    return rows(left, 3, gap=3.4), right


def paint_quarter_a_shortband(
    plotter: Plotter, box: Rect, grid: QuarterGrid, *, body: BodyRamp
) -> None:
    for cell, month in zip(quarter_seats_a_shortband(box), grid.months, strict=True):
        _paint_mini_month(plotter, cell, month, body=body)


def paint_quarter_a_note_boxes(
    plotter: Plotter, box: Rect, grid: QuarterGrid, *, body: BodyRamp
) -> None:
    for (cal, notes), month in zip(quarter_seats_a_note_boxes(box), grid.months, strict=True):
        _paint_mini_month(plotter, cal, month, body=body)
        _paint_note_box(plotter, notes, body=body)


def paint_quarter_b_stack(plotter: Plotter, box: Rect, grid: QuarterGrid, *, body: BodyRamp) -> None:
    for cell, month in zip(quarter_seats_b_stack(box), grid.months, strict=True):
        _paint_mini_month(plotter, cell, month, body=body)


def paint_quarter_c_stack_notes(
    plotter: Plotter, box: Rect, grid: QuarterGrid, *, body: BodyRamp
) -> None:
    months, notes = quarter_seats_c_stack_notes(box)
    for cell, month in zip(months, grid.months, strict=True):
        _paint_mini_month(plotter, cell, month, body=body)
    paint_notes(plotter, notes, Notes(label="Notes"), body=body)


def quarter_seats_c_focus_notes(
    box: Rect,
) -> tuple[tuple[Rect, Rect, Rect], Rect, Rect]:
    """C′: left stacked minis; right content-height Focus over flex Notes."""
    left, right = columns(box, 2, gap=3.4, weights=(0.4, 0.6))
    focus, notes = _stack_focus_notes(right)
    return rows(left, 3, gap=3.4), focus, notes


def quarter_seats_a_focus_notes(
    box: Rect,
) -> tuple[tuple[Rect, Rect, Rect], Rect, Rect]:
    """A″: short year-density month band; leftover is Focus over flex Notes."""
    cal_h = rows(box, 4, gap=2.6)[0].h
    cal_band, rest = box.split_top(cal_h)
    leftover = Rect(rest.x, rest.y + 2.6, rest.w, rest.h - 2.6)
    focus, notes = _stack_focus_notes(leftover)
    return columns(cal_band, 3, gap=4.0), focus, notes


def _stack_focus_notes(stack: Rect) -> tuple[Rect, Rect]:
    """Focus shrinks to checklist content; Notes takes the leftover."""
    gap = 2.6
    focus, rest = stack.split_top(focus_content_height())
    notes = Rect(rest.x, rest.y + gap, rest.w, rest.h - gap)
    return focus, notes


def paint_quarter_c_focus_notes(
    plotter: Plotter, box: Rect, grid: QuarterGrid, *, body: BodyRamp
) -> None:
    months, focus, notes = quarter_seats_c_focus_notes(box)
    for cell, month in zip(months, grid.months, strict=True):
        _paint_mini_month(plotter, cell, month, body=body)
    _paint_focus_box(plotter, focus, body=body)
    paint_notes(plotter, notes, Notes(label="Notes"), body=body)


def paint_quarter_a_focus_notes(
    plotter: Plotter, box: Rect, grid: QuarterGrid, *, body: BodyRamp
) -> None:
    months, focus, notes = quarter_seats_a_focus_notes(box)
    for cell, month in zip(months, grid.months, strict=True):
        _paint_mini_month(plotter, cell, month, body=body)
    _paint_focus_box(plotter, focus, body=body)
    _paint_note_box(plotter, notes, body=body, label="Notes")


def _paint_note_box(plotter: Plotter, box: Rect, *, body: BodyRamp, label: str | None = None) -> None:
    """Lined writing box — outline + daily-notes rhythm. Not a Notes section."""
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    top = 1.2
    if label:
        header_h = 3.4
        _ink_text(
            plotter,
            Rect(box.x + 1.3, box.y + 0.7, box.w - 2.6, header_h),
            label,
            body.ink("label"),
            gray=MUTED,
            small_caps=True,
        )
        top = header_h + 1.4
    inset = Rect(box.x + 1.1, box.y + top, box.w - 2.2, box.h - top - 1.2)
    pitch = 4.15
    y = inset.y + pitch
    while y < inset.bottom - 0.15:
        plotter.line(inset.x, y, inset.right, y, stroke_width=RULE, stroke_gray=RULE_C)
        y += pitch


FOCUS_ROWS = 7
TICK = 2.4
FOCUS_PITCH = 4.8
FOCUS_LABEL_H = 3.4
FOCUS_PAD_TOP = 0.8
FOCUS_PAD_MID = 1.2
FOCUS_PAD_BOT = 1.4


def checklist_content_height(rows: int, *, labeled: bool = True) -> float:
    """Tight checklist rows + pad — label band optional. Not a fraction of the parent."""
    rows_h = TICK + (max(1, rows) - 1) * FOCUS_PITCH
    pads = FOCUS_PAD_TOP + FOCUS_PAD_BOT
    if labeled:
        pads += FOCUS_LABEL_H + FOCUS_PAD_MID
    return pads + rows_h


def focus_content_height() -> float:
    return checklist_content_height(FOCUS_ROWS)


def _paint_focus_box(plotter: Plotter, box: Rect, *, body: BodyRamp) -> None:
    """Outlined FOCUS checklist — empty ticks + underline. Not a section."""
    _paint_checklist_box(plotter, box, body=body, label="Focus", rows=FOCUS_ROWS)


def paint_priorities(plotter: Plotter, box: Rect, priorities: Priorities, *, body: BodyRamp) -> None:
    _paint_checklist_box(plotter, box, body=body, label=priorities.label, rows=priorities.rows)


def _paint_checklist_box(
    plotter: Plotter, box: Rect, *, body: BodyRamp, rows: int, label: str | None = None
) -> None:
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    y = box.y + FOCUS_PAD_TOP
    if label:
        _ink_text(
            plotter,
            Rect(box.x + 1.3, box.y + FOCUS_PAD_TOP, box.w - 2.6, FOCUS_LABEL_H),
            label,
            body.ink("label"),
            gray=MUTED,
            small_caps=True,
        )
        y = box.y + FOCUS_PAD_TOP + FOCUS_LABEL_H + FOCUS_PAD_MID
    x = box.x + 1.6
    right = box.right - 1.6
    for _ in range(max(1, rows)):
        _paint_focus_row(plotter, x, y, right)
        y += FOCUS_PITCH


def _paint_focus_row(plotter: Plotter, x: float, y: float, right: float) -> None:
    tick = Rect(x, y, TICK, TICK)
    plotter.rect(tick, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    plotter.line(
        tick.right + 1.4,
        tick.bottom,
        right,
        tick.bottom,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )


def _paint_mini_month(plotter: Plotter, box: Rect, month: AnnualMonth, *, body: BodyRamp) -> None:
    pressed = month.dest is not None
    title_h = 3.5
    dow_h = 2.5
    title = Rect(box.x, box.y, box.w, title_h)
    _ink_text(
        plotter,
        title,
        month.name[:3],
        body.ink("label"),
        gray=INK if pressed else MUTED,
        small_caps=True,
        weight="bold" if pressed else None,
    )
    if month.dest:
        plotter.link(title, month.dest)
    dow = Rect(box.x, box.y + title_h, box.w, dow_h)
    tracks = columns(box, 7)
    caption = body.ink("caption")
    for i, label in enumerate(month.weekday_labels):
        col = tracks[i]
        _ink_text(
            plotter,
            Rect(col.x, dow.y, col.w, dow.h),
            label[0],
            caption,
            gray=GHOST,
            small_caps=True,
            align="center",
        )
    rule_y = dow.bottom
    plotter.line(box.x, rule_y, box.right, rule_y, stroke_width=HAIR, stroke_gray=SOFT)
    body = Rect(box.x, rule_y + 0.25, box.w, box.h - title_h - dow_h - 0.25)
    for band, week in zip(rows(body, 6), month.weeks, strict=False):
        for c, cell in enumerate(week):
            if cell.day is None:
                continue
            col = tracks[c]
            num = Rect(col.x, band.y, col.w, band.h)
            here = (
                month.highlight_day is not None
                and cell.in_month
                and cell.day == month.highlight_day
            )
            if here:
                mark = num.inset(0.12, 0.18)
                plotter.rect(mark, stroke=False, fill=True, fill_gray=INK)
                _ink_text(
                    plotter,
                    num,
                    str(cell.day),
                    caption,
                    gray=PAPER,
                    align="center",
                    weight="bold",
                )
                continue
            linked = cell.dest is not None
            ink = MUTED if not cell.in_month else (INK if linked else MUTED)
            _ink_text(
                plotter,
                num,
                str(cell.day),
                caption,
                gray=ink,
                align="center",
                weight="bold" if linked and cell.in_month else None,
            )
            if linked:
                plotter.link(num, cell.dest)


HABIT_LABEL_W = 28.0
HABIT_HEAD_H = 4.2
HABIT_HEAD_DOW_H = 7.6
HABIT_DAY_W = 13.0
HABIT_DOW_W = 5.2
HABIT_NAME_H = 16.0
HABIT_BODY_GAP = 0.5
HABIT_WASH = 247 / 255
HABIT_WASH_CROSS = 238 / 255


def habit_dow_letter(year: int, month: int, day: int) -> str:
    """Monday-start calendar letter: M T W T F S S."""
    return WEEKDAY_LABELS[date(year, month, day).weekday()][0]


def paint_habit_grid(plotter: Plotter, box: Rect, grid: HabitGrid, *, body: BodyRamp) -> None:
    """Locked default: days left with weekday, habit columns, pale zebra."""
    paint_habit_grid_transposed(plotter, box, grid, body=body)


def paint_habit_grid_rows(plotter: Plotter, box: Rect, grid: HabitGrid, *, body: BodyRamp) -> None:
    """Habits as rows, days across. Comparison only — not the default."""
    label, rest = box.split_left(HABIT_LABEL_W)
    matrix = Rect(rest.x + 1.6, rest.y, rest.w - 1.6, rest.h)
    head = Rect(box.x, box.y, box.w, HABIT_HEAD_H)
    caption = body.ink("caption")
    _ink_text(
        plotter,
        Rect(label.x, head.y, label.w, head.h),
        "Habit",
        body.ink("label"),
        gray=MUTED,
        small_caps=True,
    )
    day_heads = columns(Rect(matrix.x, head.y, matrix.w, head.h), grid.days)
    for i, col in enumerate(day_heads):
        _ink_text(plotter, col, str(i + 1), caption, gray=MUTED, align="center")
        if i < len(grid.day_dests) and grid.day_dests[i]:
            plotter.link(col, grid.day_dests[i])
    plotter.line(box.x, head.bottom, box.right, head.bottom, stroke_width=HAIR, stroke_gray=SOFT)
    body = Rect(box.x, head.bottom + 0.5, box.w, box.h - HABIT_HEAD_H - 0.5)
    bands = rows(body, max(1, grid.rows))
    day_tracks = columns(Rect(matrix.x, body.y, matrix.w, body.h), grid.days)
    for band in bands:
        plotter.line(
            label.x,
            band.bottom - 0.55,
            label.right - 0.6,
            band.bottom - 0.55,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )
        for col in day_tracks:
            cell = Rect(col.x, band.y, col.w, band.h).inset(0.16, 0.4)
            plotter.rect(cell, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)


def habit_seats_transposed(
    box: Rect, days: int, habits: int
) -> tuple[Rect, tuple[Rect, ...], tuple[Rect, ...]]:
    """Day labels left, habit name slots across the top. ``habits`` comes from the spec."""
    day_col, rest = box.split_left(HABIT_DAY_W)
    name_band, below = rest.split_top(HABIT_NAME_H)
    body = Rect(below.x, below.y + HABIT_BODY_GAP, below.w, below.h - HABIT_BODY_GAP)
    names = columns(name_band, habits, gap=0.4)
    bands = rows(body, max(1, days), gap=0.15)
    return day_col, names, bands


def paint_habit_grid_weekday_zebra(
    plotter: Plotter, box: Rect, grid: HabitGrid, *, body: BodyRamp
) -> None:
    """Habits as rows, days across. Stacked day+weekday + row zebra. Comparison only."""
    label, rest = box.split_left(HABIT_LABEL_W)
    matrix = Rect(rest.x + 1.6, rest.y, rest.w - 1.6, rest.h)
    head = Rect(box.x, box.y, box.w, HABIT_HEAD_DOW_H)
    caption = body.ink("caption")
    _ink_text(
        plotter,
        Rect(label.x, head.y, label.w, head.h),
        "Habit",
        body.ink("label"),
        gray=MUTED,
        small_caps=True,
    )
    day_heads = columns(Rect(matrix.x, head.y, matrix.w, head.h), grid.days)
    num_h = 3.8
    for i, col in enumerate(day_heads):
        day_n = i + 1
        _ink_text(
            plotter,
            Rect(col.x, col.y + 0.15, col.w, num_h),
            str(day_n),
            caption,
            gray=MUTED,
            align="center",
        )
        _ink_text(
            plotter,
            Rect(col.x, col.y + num_h - 0.1, col.w, col.h - num_h),
            habit_dow_letter(grid.year, grid.month, day_n),
            caption,
            gray=MUTED,
            align="center",
        )
        if i < len(grid.day_dests) and grid.day_dests[i]:
            plotter.link(col, grid.day_dests[i])
    plotter.line(box.x, head.bottom, box.right, head.bottom, stroke_width=HAIR, stroke_gray=SOFT)
    body = Rect(box.x, head.bottom + 0.5, box.w, box.h - HABIT_HEAD_DOW_H - 0.5)
    bands = rows(body, max(1, grid.rows))
    day_tracks = columns(Rect(matrix.x, body.y, matrix.w, body.h), grid.days)
    for i, band in enumerate(bands):
        if i % 2:
            y0, y1 = _stripe_span(bands, i, axis="y", end=box.bottom)
            _wash(plotter, Rect(box.x, y0, box.w, y1 - y0), HABIT_WASH)
        plotter.line(
            label.x,
            band.bottom - 0.55,
            label.right - 0.6,
            band.bottom - 0.55,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )
        for col in day_tracks:
            cell = Rect(col.x, band.y, col.w, band.h).inset(0.16, 0.4)
            plotter.rect(cell, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)


def _wash(plotter: Plotter, box: Rect, gray: float) -> None:
    plotter.rect(box, stroke=False, fill=True, fill_gray=gray)


def _stripe_span(tracks: tuple[Rect, ...], index: int, *, axis: str, end: float) -> tuple[float, float]:
    """Continuous zebra span covering a track plus half the neighboring gaps."""
    track = tracks[index]
    if axis == "y":
        start = (tracks[index - 1].bottom + track.y) / 2 if index else track.y
        stop = (track.bottom + tracks[index + 1].y) / 2 if index + 1 < len(tracks) else end
        return start, stop
    start = (tracks[index - 1].right + track.x) / 2 if index else track.x
    stop = (track.right + tracks[index + 1].x) / 2 if index + 1 < len(tracks) else end
    return start, stop


def paint_habit_grid_transposed(
    plotter: Plotter, box: Rect, grid: HabitGrid, *, body: BodyRamp
) -> None:
    """Days down the left (``1 W``), habit name slots across the top, pale zebra."""
    habits = max(1, grid.rows)
    day_col, names, bands = habit_seats_transposed(box, grid.days, habits)
    matrix = Rect(names[0].x, bands[0].y, names[-1].right - names[0].x, box.bottom - bands[0].y)
    day_tracks = columns(matrix, habits, gap=0.4)
    for i, _band in enumerate(bands):
        if i % 2 == 0:
            continue
        y0, y1 = _stripe_span(bands, i, axis="y", end=box.bottom)
        _wash(plotter, Rect(day_col.x, y0, box.right - day_col.x, y1 - y0), HABIT_WASH)
    for j, _col in enumerate(day_tracks):
        if j % 2 == 0:
            continue
        x0, x1 = _stripe_span(day_tracks, j, axis="x", end=day_tracks[-1].right)
        _wash(plotter, Rect(x0, names[0].y, x1 - x0, box.bottom - names[0].y), HABIT_WASH)
    for i, band in enumerate(bands):
        if i % 2 == 0:
            continue
        for j, col in enumerate(day_tracks):
            if j % 2 == 0:
                continue
            _wash(plotter, Rect(col.x, band.y, col.w, band.h), HABIT_WASH_CROSS)
    for col in names:
        plotter.line(
            col.x + 0.3,
            col.bottom - 1.1,
            col.right - 0.3,
            col.bottom - 1.1,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )
    plotter.line(box.x, names[0].bottom, box.right, names[0].bottom, stroke_width=HAIR, stroke_gray=SOFT)
    letter_w = HABIT_DOW_W
    num_w = day_col.w - letter_w
    caption = body.ink("caption")
    for i, band in enumerate(bands):
        day_n = i + 1
        _ink_text(
            plotter,
            Rect(day_col.x, band.y, num_w - 0.6, band.h),
            str(day_n),
            caption,
            gray=MUTED,
            align="right",
        )
        _ink_text(
            plotter,
            Rect(day_col.x + num_w, band.y, letter_w - 0.3, band.h),
            habit_dow_letter(grid.year, grid.month, day_n),
            caption,
            gray=MUTED,
        )
        if i < len(grid.day_dests) and grid.day_dests[i]:
            plotter.link(Rect(day_col.x, band.y, day_col.w, band.h), grid.day_dests[i])
        for col in day_tracks:
            cell = Rect(col.x, band.y, col.w, band.h).inset(0.2, 0.12)
            plotter.rect(cell, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)


def paint_month_grid(plotter: Plotter, box: Rect, grid: MonthGrid, *, body: BodyRamp) -> None:
    gutter = 8.0
    day_grid = Rect(box.x + gutter, box.y, box.w - gutter, box.h)
    tracks = columns(day_grid, 7)
    dow_h = 4.2
    header = Rect(day_grid.x, box.y, day_grid.w, dow_h)
    # Shared inset + left align for weekday letters and day numerals.
    inset = 0.5
    caption = body.ink("caption")
    day_ink = body.ink("calendar_num")
    for i, label in enumerate(grid.weekday_labels):
        col = tracks[i]
        _ink_text(
            plotter,
            Rect(col.x + inset, header.y, col.w - 2 * inset, header.h),
            label[0],
            caption,
            gray=MUTED,
            small_caps=True,
        )
    plotter.line(box.x, header.bottom, box.right, header.bottom, stroke_width=HAIR, stroke_gray=INK)

    well = Rect(box.x, header.bottom + 0.6, box.w, box.bottom - header.bottom - 0.6)
    bands = rows(well, max(1, len(grid.weeks)))
    for r, (band, week) in enumerate(zip(bands, grid.weeks, strict=False)):
        monday = _week_monday(grid, week, r)
        if monday is not None:
            iso = monday.isocalendar().week
            _ink_text(
                plotter,
                Rect(box.x, band.y, gutter - 0.4, band.h),
                f"W{iso:02d}",
                caption,
                gray=MUTED,
                small_caps=True,
            )
            if r < len(grid.week_dests) and grid.week_dests[r]:
                plotter.link(Rect(box.x, band.y, gutter, band.h), grid.week_dests[r])
        for c, day in enumerate(week):
            if day.day is None:
                continue
            col = tracks[c]
            cell = Rect(col.x, band.y, col.w, band.h)
            _ink_text(
                plotter,
                Rect(cell.x + inset, cell.y + 0.7, cell.w - 2 * inset, 5.4),
                str(day.day),
                day_ink,
            )
            if day.dest:
                plotter.link(cell, day.dest)
        plotter.line(box.x, band.bottom, box.right, band.bottom, stroke_width=HAIR, stroke_gray=SOFT)


def _week_monday(grid: MonthGrid, week: tuple, _row: int) -> date | None:
    for c, cell in enumerate(week):
        if cell.day is None:
            continue
        day = date(grid.year, grid.month, cell.day)
        return day - timedelta(days=c)
    return None


def paint_week(plotter: Plotter, box: Rect, week: WeekStrip, *, body: BodyRamp) -> None:
    label = body.ink("label")
    day_ink = body.ink("calendar_num")
    for band, day in zip(rows(box, max(1, len(week.days))), week.days, strict=False):
        ink = INK if day.in_month else MUTED
        _ink_text(
            plotter,
            Rect(band.x, band.y + 0.45, 14.0, 5.0),
            day.weekday_label,
            label,
            gray=MUTED,
            small_caps=True,
        )
        _ink_text(
            plotter,
            Rect(band.x + 14.0, band.y + 0.1, 12.0, 5.8),
            str(day.day.day),
            day_ink,
            gray=ink,
        )
        if not day.in_month or day.day.day == 1:
            _ink_text(
                plotter,
                Rect(band.x + 26.0, band.y + 0.55, 22.0, 4.8),
                MONTH_NAMES[day.day.month - 1][:3],
                label,
                gray=MUTED,
                small_caps=True,
            )
        if day.dest:
            plotter.link(Rect(band.x, band.y, band.w, 6.4), day.dest)
        rule_y = band.y + 6.9
        pitch = 4.15
        while rule_y < band.bottom - 1.15:
            plotter.line(band.x, rule_y, band.right, rule_y, stroke_width=RULE, stroke_gray=RULE_C)
            rule_y += pitch
        plotter.line(band.x, band.bottom, band.right, band.bottom, stroke_width=HAIR, stroke_gray=SOFT)


def paint_schedule(plotter: Plotter, box: Rect, schedule: Schedule, *, body: BodyRamp) -> None:
    header_h = 3.4
    _ink_text(
        plotter,
        Rect(box.x, box.y, box.w, header_h),
        schedule.label,
        body.ink("label"),
        gray=MUTED,
        small_caps=True,
    )
    well = Rect(box.x, box.y + header_h + 0.4, box.w, box.h - header_h - 0.4)
    hours = schedule.hours or (8,)
    hour_ink = body.ink("body")
    for band, hour in zip(rows(well, len(hours)), hours, strict=True):
        _ink_text(
            plotter,
            Rect(band.x, band.y, 10.0, band.h),
            f"{hour:2d}",
            hour_ink,
            gray=MUTED,
        )
        plotter.line(
            band.x,
            band.bottom,
            band.right,
            band.bottom,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )


def paint_notes(plotter: Plotter, box: Rect, notes: Notes, *, body: BodyRamp) -> None:
    header_h = 3.4
    _ink_text(
        plotter,
        Rect(box.x, box.y, box.w, header_h),
        notes.label,
        body.ink("label"),
        gray=MUTED,
        small_caps=True,
    )
    body = Rect(box.x, box.y + header_h + 0.4, box.w, box.h - header_h - 0.4)
    pitch = 4.15
    y = body.y + pitch
    while y < body.bottom - 0.15:
        plotter.line(body.x, y, body.right, y, stroke_width=RULE, stroke_gray=RULE_C)
        y += pitch


def well_rect(device: Device) -> Rect:
    """Writable well between header slab and bottom nav, inset by writing clearance."""
    top = device.content_top + HEADER_H + 2.2
    bottom = device.page_height - NAV_H - 2.2
    m = device.writing_clearance
    return Rect(m, top, device.page_width - 2 * m, bottom - top)


def strip_items(page: Page) -> tuple[tuple[str, str], ...]:
    dests: dict[str, str] = {}
    for item in page.nav:
        if item.dest.startswith("year-"):
            dests["Year"] = item.dest
        elif item.dest.startswith("quarter-"):
            dests["Quar"] = item.dest
        elif item.dest.endswith("-habits"):
            dests["Habit"] = item.dest
        elif item.dest.startswith("month-"):
            dests["Mon"] = item.dest
        elif item.dest.startswith("projects-index-"):
            dests["Proj"] = item.dest
        elif item.dest.startswith("meetings-index-"):
            dests["Meet"] = item.dest
        elif item.dest.startswith("tasks-index-"):
            dests["Task"] = item.dest
        elif item.dest.startswith("review-index-"):
            dests["Rev"] = item.dest
        elif item.dest.startswith("week-"):
            dests["Week"] = item.dest
        elif "-notes-" in item.dest:
            dests["Notes"] = item.dest
        elif item.dest.count("-") == 2 and item.dest[:4].isdigit():
            dests["Day"] = item.dest
    match page.kind:
        case "annual":
            dests["Year"] = page.dest
        case "quarter":
            dests["Quar"] = page.dest
        case "month":
            dests["Mon"] = page.dest
        case "habits":
            dests["Habit"] = page.dest
        case "projects_index":
            dests["Proj"] = page.dest
        case "project":
            pass
        case "meetings_index":
            dests["Meet"] = page.dest
        case "meeting":
            pass
        case "tasks_index":
            dests["Task"] = page.dest
        case "task":
            pass
        case "review_index":
            dests["Rev"] = page.dest
        case "review":
            pass
        case "weekly":
            dests["Week"] = page.dest
        case "daily":
            dests["Day"] = page.dest
        case "daily_notes":
            dests["Notes"] = page.dest
            dests["Day"] = page.dest.rsplit("-notes-", 1)[0]
    order = (
        "Year",
        "Quar",
        "Mon",
        "Habit",
        "Proj",
        "Meet",
        "Task",
        "Rev",
        "Week",
        "Day",
        "Notes",
    )
    return tuple((label, dests[label]) for label in order if label in dests)


def strip_active(kind: str) -> str:
    match kind:
        case "annual":
            return "Year"
        case "quarter":
            return "Quar"
        case "month":
            return "Mon"
        case "weekly":
            return "Week"
        case "daily":
            return "Day"
        case "daily_notes":
            return "Notes"
        case "habits":
            return "Habit"
        case "projects_index" | "project":
            return "Proj"
        case "meetings_index" | "meeting":
            return "Meet"
        case "tasks_index" | "task":
            return "Task"
        case "review_index" | "review":
            return "Rev"
        case _:
            return "Year"
