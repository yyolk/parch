"""Tiny Book protocol — pages(spec) plus a shared plot walk."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections.page import Page
from parch.spec import Spec


@runtime_checkable
class Book(Protocol):
    """A book is ``pages(spec)`` and ``plot(spec, plotter)``.

    ``plot_pages`` is the shared walk. Books only differ in which
    sections they concatenate.
    """

    ramp: TypeRamp

    def pages(self, spec: Spec) -> list[Page]:
        """Build the walk."""

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        """Reserve dests, then paint each page."""


def plot_pages(
    pages: Sequence[Page],
    spec: Spec,
    plotter: Plotter,
    *,
    ramp: TypeRamp,
) -> None:
    """Reserve dests, then begin/add/paint each page through PlannerLayout."""
    device = get_device(spec.device)
    layout = PlannerLayout(ramp=ramp)
    for page in pages:
        plotter.reserve_dest(page.dest)
    for page in pages:
        plotter.begin_page()
        plotter.add_dest(page.dest)
        layout.paint(page, plotter, device)
