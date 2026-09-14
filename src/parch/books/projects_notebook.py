"""Projects notebook — cover + projects index/dests. Thin Book."""

from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page, ProjectsSection
from parch.spec import Spec


class ProjectsNotebook:
    """``CoverSection`` then ``ProjectsSection``. Same plot walk as YearPlanner."""

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        return [
            *CoverSection(spec).pages(),
            *ProjectsSection(spec).pages(),
        ]

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(self.pages(spec), spec, plotter, ramp=self.ramp)
