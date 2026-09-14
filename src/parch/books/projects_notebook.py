"""Projects notebook — cover → projects index/dests (sibling of YearPlanner)."""

from dataclasses import replace

from parch.books.outline import OutlineEntry, outline_for
from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
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
                spec,
                landing_dest=spec.projects_index_dest,
                eyebrow="Projects",
                specs_lead="",
            ).pages(),
        ]
        for page in ProjectsSection(spec).pages():
            built.append(replace(page, nav=_proj_nav(page)))
        return built

    def outline_entries(self, spec: Spec) -> list[OutlineEntry]:
        return [OutlineEntry("Projects", spec.projects_index_dest)]

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=outline_for(self, spec),
        )
