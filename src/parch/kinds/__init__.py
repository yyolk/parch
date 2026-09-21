"""``PageKind`` is the union of the family unions."""

from typing import assert_never

from parch.kinds.bujo import (
    BUJO_KINDS,
    BujoKind,
    bujo_strip_active,
    exhaust_bujo_kind,
    is_bujo_kind,
)
from parch.kinds.chrome import (
    CHROME_KINDS,
    ChromeKind,
    chrome_strip_active,
    exhaust_chrome_kind,
    is_chrome_kind,
)
from parch.kinds.pad import (
    PAD_KINDS,
    PadKind,
    exhaust_pad_kind,
    is_pad_kind,
    pad_strip_active,
)
from parch.kinds.planner import (
    PLANNER_KINDS,
    PlannerKind,
    exhaust_planner_kind,
    is_planner_kind,
    planner_strip_active,
)

type PageKind = ChromeKind | PlannerKind | PadKind | BujoKind

__all__ = [
    "BUJO_KINDS",
    "CHROME_KINDS",
    "PAD_KINDS",
    "PLANNER_KINDS",
    "BujoKind",
    "ChromeKind",
    "PadKind",
    "PageKind",
    "PlannerKind",
    "exhaust_bujo_kind",
    "exhaust_chrome_kind",
    "exhaust_pad_kind",
    "exhaust_planner_kind",
    "family_strip_active",
    "is_bujo_kind",
    "is_chrome_kind",
    "is_pad_kind",
    "is_planner_kind",
]


def family_strip_active(kind: PageKind) -> str:
    """Strip label. A new family fails ``assert_never`` until it has an arm."""
    if is_chrome_kind(kind):
        return chrome_strip_active(kind)
    if is_planner_kind(kind):
        return planner_strip_active(kind)
    if is_pad_kind(kind):
        return pad_strip_active(kind)
    if is_bujo_kind(kind):
        return bujo_strip_active(kind)
    assert_never(kind)
