"""Bujo family: bullet-journal pages. Closed union is ``BujoKind``."""

from typing import Literal, TypeIs, assert_never, cast

from parch.components import (
    BujoIndex,
    BujoKey,
    CollectionLeaf,
    FutureLogPage,
    MonthlyCalendarList,
    MonthlyTaskWell,
    RapidLogPage,
)
from parch.devices.registry import Device
from parch.fonts.ramp import TypeRamp
from parch.kinds.members import literal_members
from parch.kinds.seat import PageLike, one
from parch.plotter.protocol import Plotter

type BujoKind = Literal[
    "bujo_key",
    "bujo_index",
    "future_log",
    "monthly_log",
    "monthly_tasks",
    "rapid_log",
    "collection",
]

BUJO_KINDS: frozenset[BujoKind] = cast(frozenset[BujoKind], literal_members(BujoKind))


def is_bujo_kind(kind: str) -> TypeIs[BujoKind]:
    """True when ``kind`` belongs to the bujo family."""
    return kind in BUJO_KINDS


def exhaust_bujo_kind(kind: BujoKind) -> BujoKind:
    """Closed bujo identity. A new member needs a case here."""
    match kind:
        case (
            "bujo_key"
            | "bujo_index"
            | "future_log"
            | "monthly_log"
            | "monthly_tasks"
            | "rapid_log"
            | "collection"
        ):
            return kind
        case _:
            assert_never(kind)


def bujo_strip_active(kind: BujoKind) -> str:
    """Active strip label for a bujo kind."""
    match kind:
        case "bujo_key":
            return "Key"
        case "bujo_index":
            return "Idx"
        case "future_log":
            return "Fut"
        case "monthly_log" | "monthly_tasks":
            return "Mon"
        case "rapid_log":
            return "Day"
        case "collection":
            return "Col"
        case _:
            assert_never(kind)


def bujo_header_meta(page: PageLike, kind: BujoKind) -> str:
    """Header meta for a bujo kind."""
    match kind:
        case "bujo_key":
            return page.dest.rsplit("-", 1)[-1]
        case "bujo_index":
            index = one(page, BujoIndex)
            return f"{index.page}/{index.pages}"
        case "future_log":
            future = one(page, FutureLogPage)
            return f"{future.page}/{future.pages}"
        case "monthly_log":
            return "Tasks"
        case "monthly_tasks":
            return one(page, MonthlyTaskWell).month_name[:3]
        case "rapid_log":
            return page.dest[:4]
        case "collection":
            return str(one(page, CollectionLeaf).year)
        case _:
            assert_never(kind)


def bujo_header_meta_dest(page: PageLike, kind: BujoKind) -> str | None:
    """Header meta link for a bujo kind."""
    match kind:
        case "monthly_log":
            return one(page, MonthlyCalendarList).tasks_dest
        case "monthly_tasks":
            return one(page, MonthlyTaskWell).calendar_dest
        case "bujo_key" | "bujo_index" | "future_log" | "rapid_log" | "collection":
            return None
        case _:
            assert_never(kind)


def bujo_header_chip(page: PageLike, kind: BujoKind) -> str:
    """Right-hand header chip for a bujo kind."""
    match kind:
        case "collection":
            number = one(page, CollectionLeaf).number
            return f"{number:02d}"
        case (
            "bujo_key"
            | "bujo_index"
            | "future_log"
            | "monthly_log"
            | "monthly_tasks"
            | "rapid_log"
        ):
            return ""
        case _:
            assert_never(kind)


def bujo_header_chip_dest(page: PageLike, kind: BujoKind) -> str | None:
    """Header chip link for a bujo kind."""
    match kind:
        case "collection":
            return one(page, CollectionLeaf).index_dest or None
        case (
            "bujo_key"
            | "bujo_index"
            | "future_log"
            | "monthly_log"
            | "monthly_tasks"
            | "rapid_log"
        ):
            return None
        case _:
            assert_never(kind)


def bujo_strip_dests(page: PageLike, kind: BujoKind, dests: dict[str, str]) -> None:
    """Bujo pages claim their own strip slot."""
    match kind:
        case "bujo_key":
            dests["Key"] = page.dest
        case "bujo_index":
            dests["Idx"] = page.dest
        case "future_log":
            dests["Fut"] = page.dest
        case "monthly_log" | "monthly_tasks":
            dests["Mon"] = (
                page.dest if kind == "monthly_log" else dests.get("Mon", page.dest)
            )
        case "rapid_log":
            dests["Day"] = page.dest
        case "collection":
            dests["Col"] = page.dest
        case _:
            assert_never(kind)


def paint_bujo(
    page: PageLike, plotter: Plotter, device: Device, ramp: TypeRamp, kind: BujoKind
) -> None:
    """Header, strip, and well for a bujo kind."""
    from parch.layouts.planner.painters import (
        paint_bujo_index,
        paint_bujo_key,
        paint_collection,
        paint_future_log,
        paint_header,
        paint_monthly_calendar_list,
        paint_monthly_task_well,
        paint_nav,
        paint_rapid_log,
        strip_items,
        well_rect,
    )

    paint_header(
        plotter,
        device,
        page.title,
        bujo_header_meta(page, kind),
        bujo_header_meta_dest(page, kind),
        ramp=ramp,
        chip=bujo_header_chip(page, kind),
        chip_dest=bujo_header_chip_dest(page, kind),
    )
    paint_nav(
        plotter,
        device,
        strip_items(page),
        bujo_strip_active(kind),
        ramp=ramp,
    )
    well = well_rect(device)
    match kind:
        case "bujo_key":
            paint_bujo_key(plotter, well, one(page, BujoKey), ramp=ramp)
        case "bujo_index":
            paint_bujo_index(plotter, well, one(page, BujoIndex), ramp=ramp)
        case "future_log":
            paint_future_log(plotter, well, one(page, FutureLogPage), ramp=ramp)
        case "monthly_log":
            paint_monthly_calendar_list(
                plotter, well, one(page, MonthlyCalendarList), ramp=ramp
            )
        case "monthly_tasks":
            paint_monthly_task_well(
                plotter, well, one(page, MonthlyTaskWell), ramp=ramp
            )
        case "rapid_log":
            paint_rapid_log(plotter, well, one(page, RapidLogPage), ramp=ramp)
        case "collection":
            paint_collection(plotter, well, one(page, CollectionLeaf), ramp=ramp)
        case _:
            assert_never(kind)
