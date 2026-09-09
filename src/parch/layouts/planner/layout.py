"""Planner layout: device chrome + seat, then painters."""

from parch.components import CoverTitle, MonthGrid, Notes, Schedule
from parch.devices.nomad import Device
from parch.geom import Rect
from parch.layouts.planner.painters import (
    paint_cover,
    paint_header,
    paint_month_grid,
    paint_nav,
    paint_notes,
    paint_schedule,
    paint_toolbar,
    strip_active,
    strip_items,
    well_rect,
)
from parch.plotter.protocol import Plotter
from parch.sections.page import Page

COL_GAP = 3.0


class PlannerLayout:
    """Seat components below the unmarked toolbar. Cover skips slab/nav."""

    def paint(self, page: Page, plotter: Plotter, device: Device) -> None:
        paint_toolbar(plotter, device)
        match page.kind:
            case "cover":
                paint_cover(plotter, device, _one(page, CoverTitle))
            case _:
                paint_header(plotter, device, page.title, _header_meta(page))
                paint_nav(plotter, device, strip_items(page), strip_active(page.kind))
                well = well_rect(device)
                self._paint_well(page, plotter, well)

    def _paint_well(self, page: Page, plotter: Plotter, well: Rect) -> None:
        match page.kind:
            case "month":
                paint_month_grid(plotter, well, _one(page, MonthGrid))
            case "daily":
                schedule = _one(page, Schedule)
                notes = _one(page, Notes)
                sched_w = well.w * 0.34
                left, right = well.split_left(sched_w)
                left = Rect(left.x, left.y, left.w - COL_GAP / 2, left.h)
                right = Rect(right.x + COL_GAP / 2, right.y, right.w - COL_GAP / 2, right.h)
                paint_schedule(plotter, left, schedule)
                paint_notes(plotter, right, notes)
            case "daily_notes":
                paint_notes(plotter, well, _one(page, Notes))
            case _:
                raise ValueError(f"unknown page kind {page.kind!r}")


def _header_meta(page: Page) -> str:
    match page.kind:
        case "month":
            month = _one(page, MonthGrid).month
            return f"Q{(month - 1) // 3 + 1}"
        case "daily":
            return page.dest[:4]
        case "daily_notes":
            label = _one(page, Notes).label
            return label.rsplit(" ", 1)[-1] if " " in label else page.dest[:4]
        case _:
            return ""


def _one[T](page: Page, typ: type[T]) -> T:
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")
