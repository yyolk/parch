"""Chrome family: the book frame. Closed union is ``ChromeKind``."""

from typing import Literal, TypeIs, assert_never, cast

from parch.components import CoverTitle
from parch.devices.registry import Device
from parch.fonts.ramp import TypeRamp
from parch.kinds.members import literal_members
from parch.kinds.seat import PageLike, one
from parch.plotter.protocol import Plotter

type ChromeKind = Literal["cover"]

CHROME_KINDS: frozenset[ChromeKind] = cast(
    frozenset[ChromeKind], literal_members(ChromeKind)
)


def is_chrome_kind(kind: str) -> TypeIs[ChromeKind]:
    """True when ``kind`` belongs to the chrome family."""
    return kind in CHROME_KINDS


def exhaust_chrome_kind(kind: ChromeKind) -> ChromeKind:
    """Closed chrome identity. A new member needs a case here."""
    match kind:
        case "cover":
            return kind
        case _:
            assert_never(kind)


def chrome_strip_active(kind: ChromeKind) -> str:
    """Cover keeps the historical fallback label. Layout does not ask."""
    match kind:
        case "cover":
            return "Year"
        case _:
            assert_never(kind)


def paint_chrome(
    page: PageLike, plotter: Plotter, device: Device, ramp: TypeRamp, kind: ChromeKind
) -> None:
    """Paint a chrome page. No planner header."""
    from parch.layouts.planner.painters import paint_cover

    match kind:
        case "cover":
            paint_cover(plotter, device, one(page, CoverTitle), ramp=ramp)
        case _:
            assert_never(kind)
