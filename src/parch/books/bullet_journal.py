"""Bullet journal — cover → key → index → future log → monthly cal+tasks+habits → rapid-log → collections."""

from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page
from parch.sections.bujo import (
    BujoHabitSection,
    BujoIndexSection,
    BujoKeySection,
    CollectionSection,
    FutureLogSection,
    MonthlyLogSection,
    RapidLogSection,
)
from parch.spec import Spec


class BulletJournal:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        monthly = MonthlyLogSection(spec)
        habits = BujoHabitSection(spec)
        rapid = RapidLogSection(spec)
        built = [
            *CoverSection(
                spec,
                landing_dest=spec.bujo_key_dest,
                display_title="Bullet Journal",
                specs_lead="",
            ).pages(),
            *BujoKeySection(spec).pages(),
            *BujoIndexSection(spec).pages(),
            *FutureLogSection(spec).pages(),
        ]
        for month in spec.months:
            built.extend(monthly.pages_for(month))
            built.extend(habits.pages_for(month))
            built.extend(rapid.pages_for(month))
        built.extend(CollectionSection(spec).pages())
        return built

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=spec.outline,
            top_clearance=spec.top_clearance,
        )
