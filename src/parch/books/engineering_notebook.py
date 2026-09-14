"""Engineering notebook — cover → N duplex pad sheets (sibling of YearPlanner)."""

from dataclasses import dataclass, field

from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, EngineeringPadSection, Page
from parch.spec import Spec


@dataclass(frozen=True, slots=True)
class EngineeringNotebook:
    """Cover + ``EngineeringPadSection`` only. Satisfies ``Book`` structurally."""

    ramp: TypeRamp = field(default_factory=EffectiveRamp)

    def pages(self, spec: Spec) -> list[Page]:
        landing = (
            spec.dest_for_engineering_pad(1, "front")
            if spec.engineering_sheets
            else spec.cover_dest
        )
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
        plot_pages(self.pages(spec), spec, plotter, ramp=self.ramp)
