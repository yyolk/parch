"""Painters take ``plotter: Plotter``. Components never draw themselves."""

from datetime import date, timedelta

from parch.components import CoverTitle, MonthGrid, Notes, Schedule
from parch.devices.nomad import Device
from parch.geom import Rect
from parch.plotter.protocol import Plotter
from parch.sections.page import NavItem, Page

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


def paint_header(plotter: Plotter, device: Device, title: str, meta: str) -> None:
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


def paint_month_grid(plotter: Plotter, box: Rect, grid: MonthGrid) -> None:
    gutter = 8.0
    grid_x = box.x + gutter
    grid_w = box.w - gutter
    col_w = grid_w / 7
    dow_h = 4.2
    header = Rect(grid_x, box.y, grid_w, dow_h)
    for i, label in enumerate(grid.weekday_labels):
        cell = Rect(header.x + i * col_w, header.y, col_w, header.h)
        plotter.text(
            cell,
            label[0],
            size=6.6,
            face="sans",
            gray=MUTED,
            small_caps=True,
            align="center",
        )
    plotter.line(box.x, header.bottom, box.right, header.bottom, stroke_width=HAIR, stroke_gray=INK)

    body_y = header.bottom + 0.6
    rows = max(1, len(grid.weeks))
    row_h = (box.bottom - body_y) / rows
    for r, week in enumerate(grid.weeks):
        y = body_y + r * row_h
        monday = _week_monday(grid, week, r)
        if monday is not None:
            iso = monday.isocalendar().week
            plotter.text(
                Rect(box.x, y, gutter - 0.4, row_h),
                f"W{iso:02d}",
                size=5.8,
                face="sans",
                gray=MUTED,
                small_caps=True,
                align="left",
            )
        for c, day in enumerate(week):
            if day.day is None:
                continue
            cx = grid_x + c * col_w
            num = Rect(cx + 0.5, y + 0.7, col_w - 1.0, 5.4)
            if day.dest:
                mark = Rect(cx + 0.35, y + 0.55, 7.2, 5.8)
                plotter.rect(mark, stroke=False, fill=True, fill_gray=INK)
                plotter.text(
                    num, str(day.day), size=8.5, bold=True, face="sans", gray=PAPER, align="left"
                )
                plotter.link(Rect(cx, y, col_w, row_h), day.dest)
            else:
                plotter.text(
                    num, str(day.day), size=8.5, bold=True, face="sans", gray=INK, align="left"
                )
        plotter.line(box.x, y + row_h, box.right, y + row_h, stroke_width=HAIR, stroke_gray=SOFT)


def _week_monday(grid: MonthGrid, week: tuple, _row: int) -> date | None:
    for c, cell in enumerate(week):
        if cell.day is None:
            continue
        day = date(grid.year, grid.month, cell.day)
        return day - timedelta(days=c)
    return None


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
    row_h = body.h / len(hours)
    for i, hour in enumerate(hours):
        y = body.y + i * row_h
        plotter.text(
            Rect(body.x, y, 10.0, row_h),
            f"{hour:2d}",
            size=7,
            face="sans",
            gray=MUTED,
            align="left",
        )
        plotter.line(
            body.x,
            y + row_h,
            body.right,
            y + row_h,
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
    dests: dict[str, str] = {"Cover": "cover"}
    for item in page.nav:
        if item.dest.startswith("month-"):
            dests["Mon"] = item.dest
        elif "-notes-" in item.dest:
            dests["Notes"] = item.dest
        elif item.dest.count("-") == 2 and item.dest[:4].isdigit():
            dests["Day"] = item.dest
    match page.kind:
        case "month":
            dests["Mon"] = page.dest
        case "daily":
            dests["Day"] = page.dest
        case "daily_notes":
            dests["Notes"] = page.dest
            dests["Day"] = page.dest.rsplit("-notes-", 1)[0]
    order = ("Cover", "Mon", "Day", "Notes")
    return tuple((label, dests[label]) for label in order if label in dests)


def strip_active(kind: str) -> str:
    match kind:
        case "month":
            return "Mon"
        case "daily":
            return "Day"
        case "daily_notes":
            return "Notes"
        case _:
            return "Cover"
