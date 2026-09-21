"""Missing WellKind arm: static checkers must reject this."""

from typing import assert_never

from parch.sections.page_kind import WellKind


def paint_well(kind: WellKind) -> str:
    match kind:
        case "annual":
            return "annual"
        case _ as unreachable:
            assert_never(unreachable)
