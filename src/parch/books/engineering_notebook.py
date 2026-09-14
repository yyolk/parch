"""Engineering notebook — cover → duplex pad faces (sibling of ProjectsNotebook)."""

from parch.books.plot import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, EngineeringPadSection, Page
from parch.spec import Spec


class EngineeringNotebook:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        landing = spec.dest_for_engineering_pad(1, "front")
        return [
            *CoverSection(
                spec,
                landing_dest=landing,
                eyebrow="Engineering",
                specs_lead="",
            ).pages(),
            *EngineeringPadSection(spec).pages(),
        ]

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(self.pages(spec), spec, plotter, self.ramp)
