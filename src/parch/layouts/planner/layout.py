"""Planner layout: device chrome + seat, then painters."""

from typing import assert_never

from parch.devices.registry import Device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.kinds.bujo import is_bujo_kind, paint_bujo
from parch.kinds.chrome import is_chrome_kind, paint_chrome
from parch.kinds.pad import is_pad_kind, paint_pad
from parch.kinds.planner import is_planner_kind, paint_planner
from parch.layouts.planner.painters import (
    COL_GAP,
    DAILY_COL_WEIGHTS,
    DAILY_MINI_GAP,
    DAILY_MINI_H,
    DAILY_PRIO_GAP,
    checklist_content_height,
    daily_left_seats,
    daily_right_seats,
    well_rect,
)
from parch.plotter.protocol import Plotter
from parch.sections.page import Page

__all__ = [
    "COL_GAP",
    "DAILY_COL_WEIGHTS",
    "DAILY_MINI_GAP",
    "DAILY_MINI_H",
    "DAILY_PRIO_GAP",
    "PlannerLayout",
    "checklist_content_height",
    "daily_left_seats",
    "daily_right_seats",
    "well_rect",
]


class PlannerLayout:
    """Seat components below the INK header. Chrome and pads skip header/nav.

    Holds an explicit ``TypeRamp`` (default ``EffectiveRamp``) and binds it
    onto the plotter. Painters pass ``TypeRef`` / ink on the closed TypeStep
    ladder. Press may hand in an ``EffectiveRamp`` (defaults ⊕ toml ⊕
    proof) at ``device.root_body``. ``family`` stays on the resolved ink.
    """

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def paint(self, page: Page, plotter: Plotter, device: Device) -> None:
        """Paint one page. A new family fails ``assert_never`` until it has an arm."""
        plotter.ramp = self.ramp
        kind = page.kind
        if is_chrome_kind(kind):
            paint_chrome(page, plotter, device, self.ramp, kind)
            return
        if is_planner_kind(kind):
            paint_planner(page, plotter, device, self.ramp, kind)
            return
        if is_pad_kind(kind):
            paint_pad(page, plotter, device, self.ramp, kind)
            return
        if is_bujo_kind(kind):
            paint_bujo(page, plotter, device, self.ramp, kind)
            return
        assert_never(kind)
