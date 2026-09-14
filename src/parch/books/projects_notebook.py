"""Projects notebook — cover → projects index/dests (sibling of YearPlanner)."""

from dataclasses import replace

from parch.devices import get_device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page, ProjectsSection
from parch.sections.page import NavItem
from parch.spec import Spec


def _proj_nav(page: Page) -> tuple[NavItem, ...]:
    """Keep only the Proj chip — dests from ProjectsSection, no year-book strip."""
    kept = tuple(item for item in page.nav if item.label == "Proj")
    return kept if kept else (NavItem("Proj", page.dest),)


class ProjectsNotebook:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        built = [
            *CoverSection(
                spec, landing_dest=spec.projects_index_dest, eyebrow="Projects"
            ).pages(),
        ]
        for page in ProjectsSection(spec).pages():
            built.append(replace(page, nav=_proj_nav(page)))
        return built

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        device = get_device(spec.device)
        layout = PlannerLayout(ramp=self.ramp)
        pages = self.pages(spec)
        for page in pages:
            plotter.reserve_dest(page.dest)
        for page in pages:
            plotter.begin_page()
            plotter.add_dest(page.dest)
            layout.paint(page, plotter, device)
