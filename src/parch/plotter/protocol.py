"""Plotter protocol. Painters take ``plotter: Plotter``; they never see fpdf2."""

from pathlib import Path
from typing import Literal, Protocol

from parch.fonts.catalog import TypeFamily as TextFamily, TypeWeight as TextWeight
from parch.fonts.ramp import TypeRamp, TypeRef
from parch.geom import Rect

type TextAlign = Literal["left", "center", "right"]
type TextFace = Literal["sans", "serif"]


class Plotter(Protocol):
    """Drawing surface. ``ramp`` is bound by ``PlannerLayout`` / press.

    Preferred text path: ``text(..., ref=TypeRef(...))``. The plotter asks
    ``self.ramp.resolve(ref)`` — painters never see weights. Legacy
    ``face`` + ``bold`` stay for unmigrated wells only.
    """

    ramp: TypeRamp

    def begin_page(self) -> None:
        """Start a new page. Destinations bind to the current page."""

    def reserve_dest(self, name: str) -> None:
        """Reserve a named destination so earlier pages can link to it."""

    def add_dest(self, name: str) -> None:
        """Bind a named destination to the current page."""

    def rect(
        self,
        box: Rect,
        *,
        stroke: bool = True,
        fill: bool = False,
        stroke_width: float = 0.2,
        fill_gray: float = 0.92,
        stroke_gray: float = 0.0,
    ) -> None:
        """Stroke and/or fill a rectangle. Grays are 0 black … 1 white."""

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke_width: float = 0.2,
        stroke_gray: float = 0.0,
    ) -> None:
        """Stroke a segment."""

    def text(
        self,
        box: Rect,
        content: str,
        *,
        ref: TypeRef | None = None,
        size: float = 10,
        align: TextAlign = "left",
        bold: bool = False,
        face: TextFace = "sans",
        gray: float = 0.0,
        small_caps: bool = False,
        weight: TextWeight | None = None,
        family: TextFamily | None = None,
    ) -> None:
        """Draw a single line of text inside ``box`` (pt size).

        Two-phase path: pass ``ref``. The plotter resolves it through
        ``self.ramp`` and ignores ``face`` / ``bold`` / ``family`` /
        ``weight`` / ``size``. Unmigrated painters omit ``ref`` and keep
        ``face`` + ``bold`` (Jost Book / Bold / Medium / Heavy via
        ``resolve_weight``).
        """

    def link(self, box: Rect, dest: str) -> None:
        """Invisible hit target to a named destination."""

    def finish(self, path: Path) -> None:
        """Write the document to ``path``."""
