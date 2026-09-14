"""Book protocol + shared page-ledger walk.

A book is a plain struct that structurally satisfies ``Book`` — ``ramp``,
``pages(spec)``, ``plot(spec, plotter)``. No base class. ``plot_pages`` is
the one reserve → begin / add dest / paint loop.
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.progress import render_progress
from parch.sections.page import Page
from parch.spec import Spec


@runtime_checkable
class Book(Protocol):
    """Page ledger + plot. Press dispatches; books do not inherit this."""

    ramp: TypeRamp

    def pages(self, spec: Spec) -> list[Page]:
        """Build the walk in press order."""

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        """Reserve dests, then paint each page."""


def plot_pages(
    pages: Sequence[Page],
    spec: Spec,
    plotter: Plotter,
    *,
    ramp: TypeRamp,
) -> None:
    """Walk the page ledger: reserve dests, then begin / add dest / paint.

    Progress ticks match the historical book-local ``render_progress`` calls.
    """
    device = get_device(spec.device)
    layout = PlannerLayout(ramp=ramp)
    n = len(pages)
    for page in pages:
        plotter.reserve_dest(page.dest)
    for i, page in enumerate(pages, start=1):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        layout.paint(page, plotter, device)
        render_progress(i, n, page.kind)
