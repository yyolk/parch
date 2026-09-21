"""Pad family: coverless writing faces. Closed union is ``PadKind``."""

from typing import Literal, TypeIs, assert_never, cast

from parch.components import DotGridPad, EngineeringPad, LinedPad, StenoPad
from parch.devices.registry import Device
from parch.fonts.ramp import TypeRamp
from parch.kinds.members import literal_members
from parch.kinds.seat import PageLike, one
from parch.plotter.protocol import Plotter

type PadKind = Literal[
    "engineering_front",
    "engineering_back",
    "steno",
    "dotgrid",
    "lined",
]

PAD_KINDS: frozenset[PadKind] = cast(frozenset[PadKind], literal_members(PadKind))


def is_pad_kind(kind: str) -> TypeIs[PadKind]:
    """True when ``kind`` belongs to the pad family."""
    return kind in PAD_KINDS


def exhaust_pad_kind(kind: PadKind) -> PadKind:
    """Closed pad identity. A new member needs a case here."""
    match kind:
        case "engineering_front" | "engineering_back" | "steno" | "dotgrid" | "lined":
            return kind
        case _:
            assert_never(kind)


def pad_strip_active(kind: PadKind) -> str:
    """Pads have no planner strip."""
    match kind:
        case "engineering_front" | "engineering_back" | "steno" | "dotgrid" | "lined":
            return ""
        case _:
            assert_never(kind)


def paint_pad(
    page: PageLike, plotter: Plotter, device: Device, ramp: TypeRamp, kind: PadKind
) -> None:
    """Paint a pad face. No planner header."""
    from parch.layouts.planner.painters import (
        paint_dotgrid_page,
        paint_engineering_pad,
        paint_lined_page,
        paint_steno_pad,
    )

    match kind:
        case "engineering_front" | "engineering_back":
            paint_engineering_pad(plotter, device, one(page, EngineeringPad), ramp=ramp)
        case "steno":
            paint_steno_pad(plotter, device, one(page, StenoPad), ramp=ramp)
        case "dotgrid":
            paint_dotgrid_page(plotter, device, one(page, DotGridPad), ramp=ramp)
        case "lined":
            paint_lined_page(plotter, device, one(page, LinedPad), ramp=ramp)
        case _:
            assert_never(kind)
