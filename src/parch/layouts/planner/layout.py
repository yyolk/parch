"""Planner layout: device chrome + seat, then painters."""

from parch.components import CoverTitle, MonthGrid, Notes, Schedule
from parch.devices.nomad import Device
from parch.geom import Rect
from parch.layouts.planner.painters import (
    paint_chrome,
    paint_cover,
    paint_month_grid,
    paint_notes,
    paint_schedule,
    paint_toolbar,
)
from parch.plotter.protocol import Plotter
from parch.sections.page import Page

CHROME_H = 9.0
WELL_GAP = 2.0
COL_GAP = 3.0


class PlannerLayout:
    """Seat components in the content frame. Toolbar slab stays reserved."""

    def paint(self, page: Page, plotter: Plotter, device: Device) -> None:
        paint_toolbar(plotter, device)
        frame = device.content_frame()
        chrome, rest = frame.split_top(CHROME_H)
        paint_chrome(plotter, chrome, page.title, page.nav)
        well = Rect(rest.x, rest.y + WELL_GAP, rest.w, rest.h - WELL_GAP)
        self._paint_well(page, plotter, well)

    def _paint_well(self, page: Page, plotter: Plotter, well: Rect) -> None:
        match page.kind:
            case "cover":
                paint_cover(plotter, well, _one(page, CoverTitle))
            case "month":
                paint_month_grid(plotter, well, _one(page, MonthGrid))
            case "daily":
                schedule = _one(page, Schedule)
                notes = _one(page, Notes)
                sched_w = well.w * 0.40
                left, right = well.split_left(sched_w)
                left = Rect(left.x, left.y, left.w - COL_GAP / 2, left.h)
                right = Rect(right.x + COL_GAP / 2, right.y, right.w - COL_GAP / 2, right.h)
                paint_schedule(plotter, left, schedule)
                paint_notes(plotter, right, notes)
            case "daily_notes":
                paint_notes(plotter, well, _one(page, Notes))
            case _:
                raise ValueError(f"unknown page kind {page.kind!r}")


def _one[T](page: Page, typ: type[T]) -> T:
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")
