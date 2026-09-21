"""Planner layout: device chrome + seat, then painters."""

from typing import assert_never

from parch.devices.registry import Device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.layouts.planner.kind_plan import kind_plan
from parch.layouts.planner.painters import (
    COL_GAP,
    DAILY_COL_WEIGHTS,
    DAILY_MINI_GAP,
    DAILY_MINI_H,
    DAILY_PRIO_GAP,
    checklist_content_height,
    daily_left_seats,
    daily_right_seats,
    paint_header,
    paint_nav,
    strip_items,
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
    """Seat components below the INK header. Cover and pad faces skip header/nav.

    Holds an explicit ``TypeRamp`` (default ``EffectiveRamp``) and binds it
    onto the plotter. Painters pass ``TypeRef`` / ink on the closed TypeStep
    ladder. Press may hand in an ``EffectiveRamp`` (defaults ⊕ toml ⊕
    proof) at ``device.root_body``. ``family`` stays on the resolved ink.
    """

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def paint(self, page: Page, plotter: Plotter, device: Device) -> None:
        plotter.ramp = self.ramp
        plan = kind_plan(page.kind)
        match plan.frame:
            case "bleed":
                plan.ink(plotter, device, page, self.ramp, None)
            case "chrome":
                overlay = plan.overlay(page)
                paint_header(
                    plotter,
                    device,
                    page.title,
                    overlay.meta,
                    overlay.meta_dest,
                    ramp=self.ramp,
                    chip=overlay.chip,
                    chip_dest=overlay.chip_dest,
                )
                paint_nav(
                    plotter,
                    device,
                    strip_items(page),
                    plan.strip,
                    ramp=self.ramp,
                )
                plan.ink(plotter, device, page, self.ramp, well_rect(device))
            case _:
                assert_never(plan.frame)
