"""Missing PageFace arm: static checkers must reject this."""

from typing import assert_never

from parch.sections.kind_table import page_face
from parch.sections.page_kind import PageKind


def paint(kind: PageKind) -> str:
    match page_face(kind):
        case "cover":
            return "cover"
        case "well":
            return "well"
        case _ as unreachable:
            assert_never(unreachable)
