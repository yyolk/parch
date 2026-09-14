"""Engineering notebook — thin shell around EngineeringNotebookSection."""

from parch.devices import get_device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.progress import render_progress
from parch.sections.engineering_notebook import EngineeringNotebookSection
from parch.sections.page import Page
from parch.spec import Spec


class EngineeringNotebook:
    """Press plots this book's pages; ``pages()`` is the composite section only."""

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        return EngineeringNotebookSection(spec).pages()

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        device = get_device(spec.device)
        layout = PlannerLayout(ramp=self.ramp)
        pages = self.pages(spec)
        n = len(pages)
        for page in pages:
            plotter.reserve_dest(page.dest)
        for i, page in enumerate(pages, start=1):
            plotter.begin_page()
            plotter.add_dest(page.dest)
            layout.paint(page, plotter, device)
            render_progress(i, n, page.kind)
