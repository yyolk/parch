"""Painters take ``plotter: Plotter``. Components never draw themselves."""

from datetime import date, timedelta

from parch.calendar import MONTH_NAMES, WEEKDAY_LABELS
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    CoverTitle,
    HabitGrid,
    MonthGrid,
    Notes,
    Priorities,
    ProjectsBoard,
    QuarterGrid,
    Schedule,
    WeekStrip,
)
from parch.devices.nomad import Device
from parch.geom import Rect
from parch.plotter.protocol import Plotter
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


def paint_toolbar(_plotter: Plotter, _device: Device) -> None:
    """Nomad top 8 mm stays reserved and unmarked. No fill, no label."""


def paint_header(
    plotter: Plotter,
    device: Device,
    title: str,
    meta: str,
    meta_dest: str | None = None,
    *,
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
    plotter.text(title_box, title, size=11, bold=True, face="serif", gray=PAPER, align="left")
    if chip:
        chip_box = Rect(device.page_width - gutter - meta_w - chip_w - 1.2, slab.y, chip_w, slab.h)
        plotter.text(
            chip_box, chip, size=7.4, face="sans", gray=SOFT, align="right", small_caps=True
        )
        if chip_dest:
            plotter.link(chip_box, chip_dest)
    if meta:
        meta_box = Rect(device.page_width - gutter - meta_w, slab.y, meta_w, slab.h)
        plotter.text(
            meta_box, meta, size=7.4, face="sans", gray=SOFT, align="right", small_caps=True
        )
        if meta_dest:
            plotter.link(meta_box, meta_dest)


def paint_nav(
    plotter: Plotter,
    device: Device,
    items: tuple[tuple[str, str], ...],
    active: str,
) -> None:
    if not items:
        return
    y = device.page_height - NAV_H
    slot = device.page_width / len(items)
    plotter.rect(Rect(0.0, y, device.page_width, NAV_H), stroke=False, fill=True, fill_gray=WASH)
    for i, (label, dest) in enumerate(items):
        x = i * slot
        hit = Rect(x, y, slot, NAV_H)
        on = label == active
        if on:
            plotter.rect(hit, stroke=False, fill=True, fill_gray=INK)
        plotter.text(
            hit,
            label,
            size=7.6,
            bold=on,
            face="sans",
            gray=PAPER if on else INK,
            small_caps=True,
            align="center",
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


def paint_cover(plotter: Plotter, device: Device, cover: CoverTitle) -> None:
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
    plotter.text(
        brow, "Year Book", size=10, face="serif", gray=MUTED, small_caps=True, align="center"
    )
    year_box = Rect(0.0, 56.0, device.page_width, 20.0)
    plotter.text(
        year_box, str(cover.year), size=42, bold=True, face="serif", gray=INK, align="center"
    )
    tap_w = 48.0
    plotter.link(
        Rect((device.page_width - tap_w) / 2, year_box.y, tap_w, year_box.h),
        cover.cta_dest,
    )
    specs = Rect(device.writing_clearance, 84.0, device.page_width - 2 * device.writing_clearance, 6.5)
    plotter.text(
        specs,
        f"monday weeks  ·  {device.page_width:g} × {device.page_height:g} mm",
        size=8.2,
        face="sans",
        gray=MUTED,
        small_caps=True,
        align="center",
    )


def paint_annual(plotter: Plotter, box: Rect, grid: AnnualGrid) -> None:
    for r, band in enumerate(rows(box, 4, gap=2.6)):
        for c, cell in enumerate(columns(band, 3, gap=3.4)):
            _paint_mini_month(plotter, cell, grid.months[r * 3 + c])


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
PROJECT_NOTE_PITCH = 4.15
PROJECT_STATUS_LABELS = ("Todo", "Doing", "Done")


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


def paint_projects(plotter: Plotter, box: Rect, board: ProjectsBoard) -> None:
    """Exploratory Projects well — stacked cards, no spine/arrows/graph."""
    for card in project_card_seats(box, board.cards):
        plotter.rect(card, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
        left, right = project_card_columns(card)
        header, tasks, status = project_card_left_seats(left)
        rule_y = _paint_project_name(plotter, header)
        _paint_project_tasks(plotter, tasks, board.tasks)
        _paint_project_status(plotter, status)
        _paint_project_notes(plotter, right, first_y=rule_y)


def _paint_project_name(plotter: Plotter, header: Rect) -> float:
    y = header.y + (header.h - PROJECT_P) / 2
    mark = Rect(header.x, y, PROJECT_P, PROJECT_P)
    plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    plotter.text(mark, "P", size=7.6, bold=True, face="serif", gray=INK, align="center")
    rule_y = mark.bottom
    plotter.line(
        mark.right + 1.4,
        rule_y,
        header.right,
        rule_y,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )
    return rule_y


def _paint_project_tasks(plotter: Plotter, box: Rect, n: int) -> None:
    y = box.y + 0.4
    right = box.right
    for _ in range(max(1, n)):
        _paint_focus_row(plotter, box.x, y, right)
        y += FOCUS_PITCH


def _paint_project_status(plotter: Plotter, box: Rect) -> None:
    """Orthogonal Todo / Doing / Done — open squares, tiny scaps. No arrows."""
    for slot, label in zip(columns(box, 3, gap=1.2), PROJECT_STATUS_LABELS, strict=True):
        mark_y = slot.y + (slot.h - PROJECT_STATUS_MARK) / 2
        mark = Rect(slot.x, mark_y, PROJECT_STATUS_MARK, PROJECT_STATUS_MARK)
        plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
        plotter.text(
            Rect(mark.right + 0.7, slot.y, max(slot.right - mark.right - 0.7, 1), slot.h),
            label,
            size=5.4,
            face="sans",
            gray=MUTED,
            small_caps=True,
            align="left",
        )


def _paint_project_notes(plotter: Plotter, box: Rect, *, first_y: float) -> None:
    """Lined notes pocket — same rhythm as daily notes, no graph fill."""
    y = first_y
    while y < box.bottom - 0.15:
        plotter.line(box.x, y, box.right, y, stroke_width=RULE, stroke_gray=RULE_C)
        y += PROJECT_NOTE_PITCH


STATUS_STRIP_HEAD_H = 8.4
STATUS_STRIP_MIN = 6.4
STATUS_STRIP_INSET = 1.5


def project_status_strip_seats(box: Rect) -> tuple[Rect, tuple[Rect, Rect, Rect]]:
    """Legend band over three equal status lanes. Comparison only."""
    legend, body = box.split_top(STATUS_STRIP_HEAD_H)
    todo, doing, done = columns(body, 3)
    return legend, (todo, doing, done)


def project_status_strip_legend_slots(legend: Rect) -> tuple[Rect, Rect, Rect]:
    """Todo | Doing | Done filter chips — same column tracks as the lanes."""
    todo, doing, done = columns(legend, 3)
    return todo, doing, done


def project_status_strip_name_box(lane: Rect) -> Rect:
    """Quiet inset inside a status lane before name-line tracks."""
    return Rect(
        lane.x + STATUS_STRIP_INSET,
        lane.y + 0.6,
        lane.w - 2 * STATUS_STRIP_INSET,
        lane.h - 1.0,
    )


def project_status_strip_name_rows(lane: Rect) -> tuple[Rect, ...]:
    """Project-name strips that fill a status lane. Comparison only."""
    n = max(1, int(lane.h // STATUS_STRIP_MIN))
    return rows(lane, n)


def paint_projects_status_strips(plotter: Plotter, box: Rect, board: ProjectsBoard) -> None:
    """Thesis E — status-first swim lanes. Comparison only — not the default.

    Horizontal Todo → Doing → Done as three wide lanes. Name lines only;
    cards/tasks knobs stay unused so the scan is “where is each project”.
    """
    _ = board
    legend, lanes = project_status_strip_seats(box)
    _wash(plotter, legend, WASH)
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    plotter.line(box.x, legend.bottom, box.right, legend.bottom, stroke_width=HAIR, stroke_gray=INK)
    slots = project_status_strip_legend_slots(legend)
    for i, (slot, lane, label) in enumerate(
        zip(slots, lanes, PROJECT_STATUS_LABELS, strict=True)
    ):
        if i:
            plotter.line(slot.x, box.y, slot.x, box.bottom, stroke_width=HAIR, stroke_gray=SOFT)
        _paint_status_strip_chip(plotter, slot, label)
        _paint_status_strip_names(plotter, lane)


def _paint_status_strip_chip(plotter: Plotter, slot: Rect, label: str) -> None:
    """Static filter chip — open mark + small-caps. No arrows."""
    mark_y = slot.y + (slot.h - PROJECT_STATUS_MARK) / 2
    mark = Rect(slot.x + STATUS_STRIP_INSET, mark_y, PROJECT_STATUS_MARK, PROJECT_STATUS_MARK)
    plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    muted = label == "Done"
    plotter.text(
        Rect(mark.right + 0.9, slot.y, max(slot.right - mark.right - 1.4, 1), slot.h),
        label,
        size=6.8,
        face="sans",
        gray=MUTED if muted else INK,
        small_caps=True,
        align="left",
    )


def _paint_status_strip_names(plotter: Plotter, lane: Rect) -> None:
    """Blank project-name rules. No task ticks — the lane is the status."""
    inset = project_status_strip_name_box(lane)
    for band in project_status_strip_name_rows(inset):
        y = band.y + band.h * 0.72
        plotter.line(inset.x, y, inset.right, y, stroke_width=RULE, stroke_gray=RULE_C)


def paint_quarter(plotter: Plotter, box: Rect, grid: QuarterGrid) -> None:
    """Default quarter seat is A″ — year-density minis, content-height Focus over flex Notes."""
    paint_quarter_a_focus_notes(plotter, box, grid)


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


def paint_quarter_a_shortband(plotter: Plotter, box: Rect, grid: QuarterGrid) -> None:
    for cell, month in zip(quarter_seats_a_shortband(box), grid.months, strict=True):
        _paint_mini_month(plotter, cell, month)


def paint_quarter_a_note_boxes(plotter: Plotter, box: Rect, grid: QuarterGrid) -> None:
    for (cal, notes), month in zip(quarter_seats_a_note_boxes(box), grid.months, strict=True):
        _paint_mini_month(plotter, cal, month)
        _paint_note_box(plotter, notes)


def paint_quarter_b_stack(plotter: Plotter, box: Rect, grid: QuarterGrid) -> None:
    for cell, month in zip(quarter_seats_b_stack(box), grid.months, strict=True):
        _paint_mini_month(plotter, cell, month)


def paint_quarter_c_stack_notes(plotter: Plotter, box: Rect, grid: QuarterGrid) -> None:
    months, notes = quarter_seats_c_stack_notes(box)
    for cell, month in zip(months, grid.months, strict=True):
        _paint_mini_month(plotter, cell, month)
    paint_notes(plotter, notes, Notes(label="Notes"))


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


def paint_quarter_c_focus_notes(plotter: Plotter, box: Rect, grid: QuarterGrid) -> None:
    months, focus, notes = quarter_seats_c_focus_notes(box)
    for cell, month in zip(months, grid.months, strict=True):
        _paint_mini_month(plotter, cell, month)
    _paint_focus_box(plotter, focus)
    paint_notes(plotter, notes, Notes(label="Notes"))


def paint_quarter_a_focus_notes(plotter: Plotter, box: Rect, grid: QuarterGrid) -> None:
    months, focus, notes = quarter_seats_a_focus_notes(box)
    for cell, month in zip(months, grid.months, strict=True):
        _paint_mini_month(plotter, cell, month)
    _paint_focus_box(plotter, focus)
    _paint_note_box(plotter, notes, label="Notes")


def _paint_note_box(plotter: Plotter, box: Rect, *, label: str | None = None) -> None:
    """Lined writing box — outline + daily-notes rhythm. Not a Notes section."""
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    top = 1.2
    if label:
        header_h = 3.4
        plotter.text(
            Rect(box.x + 1.3, box.y + 0.7, box.w - 2.6, header_h),
            label,
            size=6.4,
            face="sans",
            gray=MUTED,
            small_caps=True,
            align="left",
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


def checklist_content_height(rows: int) -> float:
    """Label + tight checklist rows + pad — not a fraction of the parent."""
    rows_h = TICK + (max(1, rows) - 1) * FOCUS_PITCH
    return FOCUS_PAD_TOP + FOCUS_LABEL_H + FOCUS_PAD_MID + rows_h + FOCUS_PAD_BOT


def focus_content_height() -> float:
    return checklist_content_height(FOCUS_ROWS)


def _paint_focus_box(plotter: Plotter, box: Rect) -> None:
    """Outlined FOCUS checklist — empty ticks + underline. Not a section."""
    _paint_checklist_box(plotter, box, label="Focus", rows=FOCUS_ROWS)


def paint_priorities(plotter: Plotter, box: Rect, priorities: Priorities) -> None:
    _paint_checklist_box(plotter, box, label=priorities.label, rows=priorities.rows)


def _paint_checklist_box(plotter: Plotter, box: Rect, *, label: str, rows: int) -> None:
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    plotter.text(
        Rect(box.x + 1.3, box.y + FOCUS_PAD_TOP, box.w - 2.6, FOCUS_LABEL_H),
        label,
        size=6.4,
        face="sans",
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    x = box.x + 1.6
    right = box.right - 1.6
    y = box.y + FOCUS_PAD_TOP + FOCUS_LABEL_H + FOCUS_PAD_MID
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


def _paint_mini_month(plotter: Plotter, box: Rect, month: AnnualMonth) -> None:
    pressed = month.dest is not None
    title_h = 3.5
    dow_h = 2.5
    title = Rect(box.x, box.y, box.w, title_h)
    plotter.text(
        title,
        month.name[:3],
        size=6.4,
        bold=pressed,
        face="sans",
        gray=INK if pressed else MUTED,
        small_caps=True,
        align="left",
    )
    if month.dest:
        plotter.link(title, month.dest)
    dow = Rect(box.x, box.y + title_h, box.w, dow_h)
    tracks = columns(box, 7)
    for i, label in enumerate(month.weekday_labels):
        col = tracks[i]
        plotter.text(
            Rect(col.x, dow.y, col.w, dow.h),
            label[0],
            size=4.3,
            face="sans",
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
                plotter.text(
                    num,
                    str(cell.day),
                    size=5.3,
                    bold=True,
                    face="sans",
                    gray=PAPER,
                    align="center",
                )
                continue
            linked = cell.dest is not None
            ink = MUTED if not cell.in_month else (INK if linked else MUTED)
            plotter.text(
                num,
                str(cell.day),
                size=5.3,
                bold=linked and cell.in_month,
                face="sans",
                gray=ink,
                align="center",
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


def paint_habit_grid(plotter: Plotter, box: Rect, grid: HabitGrid) -> None:
    """Locked default: days left with weekday, habit columns, pale zebra."""
    paint_habit_grid_transposed(plotter, box, grid)


def paint_habit_grid_rows(plotter: Plotter, box: Rect, grid: HabitGrid) -> None:
    """Habits as rows, days across. Comparison only — not the default."""
    label, rest = box.split_left(HABIT_LABEL_W)
    matrix = Rect(rest.x + 1.6, rest.y, rest.w - 1.6, rest.h)
    head = Rect(box.x, box.y, box.w, HABIT_HEAD_H)
    plotter.text(
        Rect(label.x, head.y, label.w, head.h),
        "Habit",
        size=5.8,
        face="sans",
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    day_heads = columns(Rect(matrix.x, head.y, matrix.w, head.h), grid.days)
    for i, col in enumerate(day_heads):
        plotter.text(
            col,
            str(i + 1),
            size=3.8,
            face="sans",
            gray=MUTED,
            align="center",
        )
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


def paint_habit_grid_weekday_zebra(plotter: Plotter, box: Rect, grid: HabitGrid) -> None:
    """Habits as rows, days across. Stacked day+weekday + row zebra. Comparison only."""
    label, rest = box.split_left(HABIT_LABEL_W)
    matrix = Rect(rest.x + 1.6, rest.y, rest.w - 1.6, rest.h)
    head = Rect(box.x, box.y, box.w, HABIT_HEAD_DOW_H)
    plotter.text(
        Rect(label.x, head.y, label.w, head.h),
        "Habit",
        size=5.8,
        face="sans",
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    day_heads = columns(Rect(matrix.x, head.y, matrix.w, head.h), grid.days)
    num_h = 3.8
    for i, col in enumerate(day_heads):
        day_n = i + 1
        plotter.text(
            Rect(col.x, col.y + 0.15, col.w, num_h),
            str(day_n),
            size=3.5,
            face="sans",
            gray=MUTED,
            align="center",
        )
        plotter.text(
            Rect(col.x, col.y + num_h - 0.1, col.w, col.h - num_h),
            habit_dow_letter(grid.year, grid.month, day_n),
            size=3.3,
            face="sans",
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


def paint_habit_grid_transposed(plotter: Plotter, box: Rect, grid: HabitGrid) -> None:
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
    for i, band in enumerate(bands):
        day_n = i + 1
        plotter.text(
            Rect(day_col.x, band.y, num_w - 0.6, band.h),
            str(day_n),
            size=4.4,
            face="sans",
            gray=MUTED,
            align="right",
        )
        plotter.text(
            Rect(day_col.x + num_w, band.y, letter_w - 0.3, band.h),
            habit_dow_letter(grid.year, grid.month, day_n),
            size=4.4,
            face="sans",
            gray=MUTED,
            align="left",
        )
        if i < len(grid.day_dests) and grid.day_dests[i]:
            plotter.link(Rect(day_col.x, band.y, day_col.w, band.h), grid.day_dests[i])
        for col in day_tracks:
            cell = Rect(col.x, band.y, col.w, band.h).inset(0.2, 0.12)
            plotter.rect(cell, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)


def paint_month_grid(plotter: Plotter, box: Rect, grid: MonthGrid) -> None:
    gutter = 8.0
    day_grid = Rect(box.x + gutter, box.y, box.w - gutter, box.h)
    tracks = columns(day_grid, 7)
    dow_h = 4.2
    header = Rect(day_grid.x, box.y, day_grid.w, dow_h)
    # Shared inset + left align for weekday letters and day numerals.
    inset = 0.5
    for i, label in enumerate(grid.weekday_labels):
        col = tracks[i]
        plotter.text(
            Rect(col.x + inset, header.y, col.w - 2 * inset, header.h),
            label[0],
            size=6.6,
            face="sans",
            gray=MUTED,
            small_caps=True,
            align="left",
        )
    plotter.line(box.x, header.bottom, box.right, header.bottom, stroke_width=HAIR, stroke_gray=INK)

    body = Rect(box.x, header.bottom + 0.6, box.w, box.bottom - header.bottom - 0.6)
    bands = rows(body, max(1, len(grid.weeks)))
    for r, (band, week) in enumerate(zip(bands, grid.weeks, strict=False)):
        monday = _week_monday(grid, week, r)
        if monday is not None:
            iso = monday.isocalendar().week
            plotter.text(
                Rect(box.x, band.y, gutter - 0.4, band.h),
                f"W{iso:02d}",
                size=5.8,
                face="sans",
                gray=MUTED,
                small_caps=True,
                align="left",
            )
            if r < len(grid.week_dests) and grid.week_dests[r]:
                plotter.link(Rect(box.x, band.y, gutter, band.h), grid.week_dests[r])
        for c, day in enumerate(week):
            if day.day is None:
                continue
            col = tracks[c]
            cell = Rect(col.x, band.y, col.w, band.h)
            plotter.text(
                Rect(cell.x + inset, cell.y + 0.7, cell.w - 2 * inset, 5.4),
                str(day.day),
                size=8.5,
                bold=True,
                face="sans",
                gray=INK,
                align="left",
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


def paint_week(plotter: Plotter, box: Rect, week: WeekStrip) -> None:
    for band, day in zip(rows(box, max(1, len(week.days))), week.days, strict=False):
        ink = INK if day.in_month else MUTED
        plotter.text(
            Rect(band.x, band.y + 0.45, 14.0, 5.0),
            day.weekday_label,
            size=6.6,
            face="sans",
            gray=MUTED,
            small_caps=True,
            align="left",
        )
        plotter.text(
            Rect(band.x + 14.0, band.y + 0.1, 12.0, 5.8),
            str(day.day.day),
            size=11,
            bold=True,
            face="sans",
            gray=ink,
            align="left",
        )
        if not day.in_month or day.day.day == 1:
            plotter.text(
                Rect(band.x + 26.0, band.y + 0.55, 22.0, 4.8),
                MONTH_NAMES[day.day.month - 1][:3],
                size=6.6,
                face="sans",
                gray=MUTED,
                small_caps=True,
                align="left",
            )
        if day.dest:
            plotter.link(Rect(band.x, band.y, band.w, 6.4), day.dest)
        rule_y = band.y + 6.9
        pitch = 4.15
        while rule_y < band.bottom - 1.15:
            plotter.line(band.x, rule_y, band.right, rule_y, stroke_width=RULE, stroke_gray=RULE_C)
            rule_y += pitch
        plotter.line(band.x, band.bottom, band.right, band.bottom, stroke_width=HAIR, stroke_gray=SOFT)


def paint_schedule(plotter: Plotter, box: Rect, schedule: Schedule) -> None:
    header_h = 3.4
    plotter.text(
        Rect(box.x, box.y, box.w, header_h),
        schedule.label,
        size=6.4,
        face="sans",
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    body = Rect(box.x, box.y + header_h + 0.4, box.w, box.h - header_h - 0.4)
    hours = schedule.hours or (8,)
    for band, hour in zip(rows(body, len(hours)), hours, strict=True):
        plotter.text(
            Rect(band.x, band.y, 10.0, band.h),
            f"{hour:2d}",
            size=7,
            face="sans",
            gray=MUTED,
            align="left",
        )
        plotter.line(
            band.x,
            band.bottom,
            band.right,
            band.bottom,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )


def paint_notes(plotter: Plotter, box: Rect, notes: Notes) -> None:
    header_h = 3.4
    plotter.text(
        Rect(box.x, box.y, box.w, header_h),
        notes.label,
        size=6.4,
        face="sans",
        gray=MUTED,
        small_caps=True,
        align="left",
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
        case "projects":
            pass
        case "weekly":
            dests["Week"] = page.dest
        case "daily":
            dests["Day"] = page.dest
        case "daily_notes":
            dests["Notes"] = page.dest
            dests["Day"] = page.dest.rsplit("-notes-", 1)[0]
    order = ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes")
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
        case "projects":
            return ""
        case _:
            return "Year"
