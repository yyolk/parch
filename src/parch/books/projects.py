"""Projects notebook — cover → projects index/dests. Reuses YearPlanner sections."""

from parch.books.protocol import plot_book
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page, ProjectsSection
from parch.spec import Spec


class ProjectsNotebook:
    """Thin Book: CoverSection + ProjectsSection only."""

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        return [
            *CoverSection(spec).pages(),
            *ProjectsSection(spec).pages(),
        ]

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_book(self, spec, plotter)
