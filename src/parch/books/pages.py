"""Page factories and the shared reserve / begin / paint walk."""

from collections.abc import Sequence
from dataclasses import replace

from parch.devices import Device
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page, ProjectsSection
from parch.spec import Spec


def plot_pages(
    pages: Sequence[Page],
    plotter: Plotter,
    device: Device,
    layout: PlannerLayout,
) -> None:
    """Reserve dests, then begin / add dest / paint each page."""
    for page in pages:
        plotter.reserve_dest(page.dest)
    for page in pages:
        plotter.begin_page()
        plotter.add_dest(page.dest)
        layout.paint(page, plotter, device)


def projects_notebook_pages(spec: Spec) -> list[Page]:
    """Cover + projects index/boards. Calls the existing section builders."""
    return [
        *CoverSection(spec, cta_dest=spec.projects_index_dest).pages(),
        *(_proj_only_nav(page) for page in ProjectsSection(spec).pages()),
    ]


def _proj_only_nav(page: Page) -> Page:
    """Keep Proj strip items so fpdf2 does not link missing year-planner dests."""
    return replace(page, nav=tuple(item for item in page.nav if item.label == "Proj"))
