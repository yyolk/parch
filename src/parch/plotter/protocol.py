"""Plotter protocol. Painters take ``plotter: Plotter``; they never see fpdf2."""

from pathlib import Path
from typing import Literal, Protocol

from parch.fonts.catalog import TypeFamily as TextFamily, TypeWeight as TextWeight
from parch.fonts.ramp import TypeFace as TextFace, TypeInk, TypeRamp, TypeRef, resolve_ref
from parch.geom import Rect

type TextAlign = Literal["left", "center", "right"]


def resolve_text_ink(
    ramp: TypeRamp,
    *,
    ink: TypeInk | None,
    ref: TypeRef | None,
) -> TypeInk | None:
    """Migrated path: exactly one of ``ink`` or ``ref``. Otherwise ``None`` (face path)."""
    if ink is not None and ref is not None:
        raise TypeError("Plotter.text migrated path takes ink= or ref=, not both")
    if ref is not None:
        return resolve_ref(ramp, ref)
    return ink


class Plotter(Protocol):
    """Drawing surface. ``ramp`` is bound by ``PlannerLayout`` / press.

    Migrated path: ``text(..., ink=)`` or ``text(..., ref=TypeRef(...))``.
    A ref is resolved once at the edge via ``resolve_ref(plotter.ramp, ref)``.
    Face / bold stay for the FaceBridge backlog only.
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
        ink: TypeInk | None = None,
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
        """Draw a single line of text inside ``box``.

        * Migrated — ``ink: TypeInk`` and/or ``ref=`` (``TypeStep`` vocabulary).
          ``ref`` resolves through ``plotter.ramp``.
        * FaceBridge backlog — omit both; ``face`` + ``bold`` + ``size`` stay
          for habit / meeting / review / tasks.
        """

    def link(self, box: Rect, dest: str) -> None:
        """Invisible hit target to a named destination."""

    def finish(self, path: Path) -> None:
        """Write the document to ``path``."""
