"""Dot-grid notebook — coverless N sheets (sibling of YearPlanner).

Exploratory DG3: explicit ``book = "dot-grid"`` selection via ``book_for``.
Not a year-planner pad hijack. Pages are full-bleed clone dots only.
"""

from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections.dot_grid import DotGridSection
from parch.sections.page import Page
from parch.spec import Spec


class DotGrid:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        return DotGridSection(spec).pages()

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=spec.outline,
            top_clearance=spec.top_clearance,
        )
