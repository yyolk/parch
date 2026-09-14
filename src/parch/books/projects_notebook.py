"""Projects notebook — cover → projects index/dests. Sibling of YearPlanner."""

from dataclasses import replace

from parch.components import CoverTitle
from parch.devices import get_device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, NavItem, Page, ProjectsSection
from parch.spec import Spec


def _proj_dest(page: Page, spec: Spec) -> str:
    """Keep the section’s index landing when present; else index page 1."""
    for item in page.nav:
        if item.dest.startswith("projects-index-"):
            return item.dest
    return spec.projects_index_dest


def _proj_nav(dest: str) -> tuple[NavItem, ...]:
    return (NavItem("Proj", dest),)


def _retarget(page: Page, spec: Spec) -> Page:
    """Reuse section components; land chrome on the projects index."""
    landing = _proj_dest(page, spec)
    components = page.components
    if page.kind == "cover":
        landing = spec.projects_index_dest
        components = tuple(
            replace(item, cta_dest=landing) if isinstance(item, CoverTitle) else item
            for item in page.components
        )
    return replace(page, nav=_proj_nav(landing), components=components)


class ProjectsNotebook:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        return [
            _retarget(page, spec)
            for page in (*CoverSection(spec).pages(), *ProjectsSection(spec).pages())
        ]

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
