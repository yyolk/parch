"""Tiny book protocol — ``pages`` + shared reserve / begin / paint."""

from collections.abc import Sequence
from typing import Protocol

from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections.page import Page
from parch.spec import Spec


class Book(Protocol):
    """A book is ``pages`` plus ``plot``. Press dispatches; no registry."""

    def pages(self, spec: Spec) -> list[Page]: ...

    def plot(self, spec: Spec, plotter: Plotter) -> None: ...


def plot_pages(
    pages: Sequence[Page], spec: Spec, plotter: Plotter, *, ramp: TypeRamp
) -> None:
    """Reserve dests, then begin / add dest / paint each page."""
    device = get_device(spec.device)
    layout = PlannerLayout(ramp=ramp)
    for page in pages:
        plotter.reserve_dest(page.dest)
    for page in pages:
        plotter.begin_page()
        plotter.add_dest(page.dest)
        layout.paint(page, plotter, device)
