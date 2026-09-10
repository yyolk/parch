"""Throwaway Thesis A book — one column-board page. Not in the year walk."""

from parch.devices import get_device
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import Page, ProjectsBoardSection
from parch.spec import Spec


class ProjectsColumnsBook:
    def pages(self, spec: Spec) -> list[Page]:
        return ProjectsBoardSection(spec).pages()

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        device = get_device(spec.device)
        layout = PlannerLayout()
        pages = self.pages(spec)
        for page in pages:
            plotter.reserve_dest(page.dest)
        for page in pages:
            plotter.begin_page()
            plotter.add_dest(page.dest)
            # Strip dests are not in this book; bind them here so fpdf2 can close.
            for item in page.nav:
                plotter.add_dest(item.dest)
            layout.paint(page, plotter, device)
