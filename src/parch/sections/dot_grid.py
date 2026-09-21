"""Optional full-bleed clone-dot extras — after tasks in YearPlanner.

Spec ``dot_grid_pages`` (default 0) inserts that many blank pages into the
year-planner walk. Not a separate pad book. Layout paints the full device
page and skips header/nav — hypothesis: no strip on these pages.
"""

from parch.components import DotGridPage
from parch.sections.page import Page
from parch.spec import Spec


class DotGridSection:
    """Emit ``spec.dot_grid_pages`` edge-to-edge clone-dot sheets. Off is empty."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        if spec.dot_grid_pages < 1:
            return []
        pages_n = spec.dot_grid_pages
        built: list[Page] = []
        for page in range(1, pages_n + 1):
            built.append(
                Page(
                    dest=spec.dest_for_dot_grid(page),
                    kind="dot_grid",
                    title="Dot grid",
                    nav=(),
                    components=(DotGridPage(page=page, pages=pages_n),),
                )
            )
        return built
