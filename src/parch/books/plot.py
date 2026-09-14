"""Shared pages → reserve → begin/add/paint walk for every book."""

from collections.abc import Sequence

from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.progress import render_progress
from parch.sections.page import Page
from parch.spec import Spec


def plot_pages(
    pages: Sequence[Page], spec: Spec, plotter: Plotter, ramp: TypeRamp
) -> None:
    """Reserve dests, then paint each page. Progress ticks match the books."""
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
