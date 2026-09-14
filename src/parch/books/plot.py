"""Shared page-paint loop for YearPlanner and ProjectsNotebook."""

from collections.abc import Callable

from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import Page
from parch.spec import Spec

type OnPage = Callable[[int, int, Page], None]


def plot_pages(
    spec: Spec,
    plotter: Plotter,
    pages: list[Page],
    ramp: TypeRamp,
    on_page: OnPage | None = None,
) -> None:
    """Reserve dests, paint each page, then call ``on_page(i, n, page)`` (1-based)."""
    device = get_device(spec.device)
    layout = PlannerLayout(ramp=ramp)
    total = len(pages)
    for page in pages:
        plotter.reserve_dest(page.dest)
    for index, page in enumerate(pages, start=1):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        layout.paint(page, plotter, device)
        if on_page is not None:
            on_page(index, total, page)
