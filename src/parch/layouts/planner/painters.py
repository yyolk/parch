"""Painters take ``plotter: Plotter``. Components never draw themselves."""

from parch.components import CoverTitle, MonthGrid, Notes, Schedule
from parch.devices.nomad import Device
from parch.geom import Rect
from parch.plotter.protocol import Plotter
from parch.sections.page import NavItem

HAIR = 0.15
RULE = 0.25


def paint_toolbar(plotter: Plotter, device: Device) -> None:
    slab = device.toolbar_slab()
    if slab is None:
        return
    plotter.rect(slab, stroke=False, fill=True, fill_gray=0.88)
    plotter.line(0.0, slab.bottom, device.page_width, slab.bottom, stroke_width=HAIR)
    plotter.text(slab, "toolbar 8 mm - not a well", size=6, align="center")


def paint_chrome(plotter: Plotter, box: Rect, title: str, nav: tuple[NavItem, ...]) -> None:
    plotter.line(box.x, box.bottom, box.right, box.bottom, stroke_width=RULE)
    if not nav:
        plotter.text(box, title, size=11, bold=True, align="left")
        return
    title_w = box.w * 0.55
    title_box, rest = box.split_left(title_w)
    plotter.text(title_box, title, size=11, bold=True, align="left")
    slot_w = rest.w / len(nav)
    for i, item in enumerate(nav):
        hit = Rect(rest.x + i * slot_w, rest.y + 1.0, slot_w - 0.8, rest.h - 2.0)
        plotter.rect(hit, stroke=True, fill=False, stroke_width=HAIR)
        plotter.text(hit, item.label, size=8, align="center")
        plotter.link(hit, item.dest)


def paint_cover(plotter: Plotter, box: Rect, cover: CoverTitle) -> None:
    year_h = 22.0
    year_box = Rect(box.x, box.y + 18.0, box.w, year_h)
    plotter.text(year_box, str(cover.year), size=32, bold=True, align="center")

    sub = Rect(box.x, year_box.bottom + 4.0, box.w, 8.0)
    plotter.text(sub, cover.subtitle, size=12, align="center")

    device = Rect(box.x, sub.bottom + 2.0, box.w, 7.0)
    plotter.text(device, cover.device_name, size=9, align="center")

    cta = Rect(box.x + box.w * 0.18, device.bottom + 14.0, box.w * 0.64, 12.0)
    plotter.rect(cta, stroke=True, fill=False, stroke_width=RULE)
    plotter.text(cta, cover.cta_label, size=11, align="center")
    plotter.link(cta, cover.cta_dest)


def paint_month_grid(plotter: Plotter, box: Rect, grid: MonthGrid) -> None:
    header_h = 7.0
    header, body = box.split_top(header_h)
    col_w = header.w / 7
    for i, label in enumerate(grid.weekday_labels):
        cell = Rect(header.x + i * col_w, header.y, col_w, header.h)
        plotter.text(cell, label, size=7, align="center", bold=True)
    plotter.line(header.x, header.bottom, header.right, header.bottom, stroke_width=RULE)

    rows = max(1, len(grid.weeks))
    row_h = body.h / rows
    for r, week in enumerate(grid.weeks):
        for c, day in enumerate(week):
            cell = Rect(body.x + c * col_w, body.y + r * row_h, col_w, row_h)
            linked = day.dest is not None
            plotter.rect(
                cell,
                stroke=True,
                fill=linked,
                stroke_width=RULE if linked else HAIR,
                fill_gray=0.94,
            )
            if day.day is not None:
                inset = cell.inset(0.6, 0.8)
                plotter.text(inset, str(day.day), size=9, align="center", bold=linked)
            if day.dest:
                plotter.link(cell, day.dest)


def paint_schedule(plotter: Plotter, box: Rect, schedule: Schedule) -> None:
    header_h = 7.0
    header, body = box.split_top(header_h)
    plotter.rect(box, stroke=True, fill=False, stroke_width=RULE)
    plotter.text(header.inset(1.2, 0), schedule.label, size=8, bold=True, align="left")
    plotter.line(header.x, header.bottom, header.right, header.bottom, stroke_width=RULE)

    hours = schedule.hours or (8,)
    row_h = body.h / len(hours)
    for i, hour in enumerate(hours):
        row = Rect(body.x, body.y + i * row_h, body.w, row_h)
        label = Rect(row.x + 1.2, row.y, 10.0, row.h)
        plotter.text(label, f"{hour:2d}", size=7, align="left")
        plotter.line(row.x, row.bottom, row.right, row.bottom, stroke_width=HAIR)


def paint_notes(plotter: Plotter, box: Rect, notes: Notes) -> None:
    header_h = 7.0
    header, body = box.split_top(header_h)
    plotter.rect(box, stroke=True, fill=False, stroke_width=RULE)
    plotter.text(header.inset(1.2, 0), notes.label, size=8, bold=True, align="left")
    plotter.line(header.x, header.bottom, header.right, header.bottom, stroke_width=RULE)

    # ~6 mm ruling — readable on Nomad, not a full year of polish.
    rule = 6.0
    y = body.y + rule
    while y < body.bottom - 0.4:
        plotter.line(body.x + 1.2, y, body.right - 1.2, y, stroke_width=HAIR)
        y += rule
