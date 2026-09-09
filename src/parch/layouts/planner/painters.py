"""Painters take ``plotter: Plotter``. Components never draw themselves."""

from datetime import date, timedelta

from parch.calendar import MONTH_NAMES
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    CoverTitle,
    MonthGrid,
    Notes,
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
) -> None:
    slab = Rect(0.0, device.content_top, device.page_width, HEADER_H)
    plotter.rect(slab, stroke=False, fill=True, fill_gray=INK)
    gutter = device.writing_clearance
    meta_w = 28.0
    title_box = Rect(gutter, slab.y, device.page_width - 2 * gutter - meta_w - 1.5, slab.h)
    plotter.text(title_box, title, size=11, bold=True, face="serif", gray=PAPER, align="left")
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


def paint_quarter(plotter: Plotter, box: Rect, grid: QuarterGrid) -> None:
    """Default seat — not locked; A″ / B / C′ are comparison variants below."""
    for cell, month in zip(columns(box, 3, gap=4.0), grid.months, strict=True):
        _paint_mini_month(plotter, cell, month)


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
    """C′: left stacked minis; right Focus (⅓) over Notes (⅔)."""
    left, right = columns(box, 2, gap=3.4, weights=(0.4, 0.6))
    focus, notes = rows(right, 2, weights=(1, 2), gap=2.6)
    return rows(left, 3, gap=3.4), focus, notes


def quarter_seats_a_focus_notes(
    box: Rect,
) -> tuple[tuple[Rect, Rect, Rect], Rect, Rect]:
    """A″: short year-density month band; leftover is Focus over Notes."""
    cal_h = rows(box, 4, gap=2.6)[0].h
    cal_band, rest = box.split_top(cal_h)
    leftover = Rect(rest.x, rest.y + 2.6, rest.w, rest.h - 2.6)
    focus, notes = rows(leftover, 2, gap=2.6)
    return columns(cal_band, 3, gap=4.0), focus, notes


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


FOCUS_ROWS = 6
TICK = 2.4
FOCUS_PITCH = 5.4


def _paint_focus_box(plotter: Plotter, box: Rect) -> None:
    """Outlined FOCUS checklist — empty ticks + underline. Not a section."""
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    header_h = 3.4
    plotter.text(
        Rect(box.x + 1.3, box.y + 0.7, box.w - 2.6, header_h),
        "Focus",
        size=6.4,
        face="sans",
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    body = Rect(
        box.x + 1.6,
        box.y + header_h + 1.4,
        box.w - 3.2,
        box.h - header_h - 2.6,
    )
    if FOCUS_ROWS * FOCUS_PITCH <= body.h:
        y = body.y
        for _ in range(FOCUS_ROWS):
            _paint_focus_row(plotter, body.x, y, body.right)
            y += FOCUS_PITCH
        return
    for band in rows(body, FOCUS_ROWS, gap=0.7):
        _paint_focus_row(plotter, band.x, band.y, band.right)


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
            linked = cell.dest is not None
            plotter.text(
                num,
                str(cell.day),
                size=5.3,
                bold=linked,
                face="sans",
                gray=INK if linked else MUTED,
                align="center",
            )
            if linked:
                plotter.link(num, cell.dest)


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
        case "weekly":
            dests["Week"] = page.dest
        case "daily":
            dests["Day"] = page.dest
        case "daily_notes":
            dests["Notes"] = page.dest
            dests["Day"] = page.dest.rsplit("-notes-", 1)[0]
    order = ("Year", "Quar", "Mon", "Week", "Day", "Notes")
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
        case _:
            return "Year"
