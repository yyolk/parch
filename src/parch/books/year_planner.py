"""Year planner book — cover → one month → each day (+ notes wells)."""

from parch.calendar import month_days
from parch.devices import get_device
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, DailyNotesSection, DailySection, MonthSection, Page
from parch.spec import Spec


class YearPlanner:
    def pages(self, spec: Spec) -> list[Page]:
        daily = DailySection(spec)
        notes = DailyNotesSection(spec)
        built = [
            *CoverSection(spec).pages(),
            *MonthSection(spec).pages(),
        ]
        for day in month_days(spec.year, spec.month):
            built.extend(daily.pages_for(day))
            built.extend(notes.pages_for(day))
        return built

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        device = get_device(spec.device)
        layout = PlannerLayout()
        pages = self.pages(spec)
        for page in pages:
            plotter.reserve_dest(page.dest)
        for page in pages:
            plotter.begin_page()
            plotter.add_dest(page.dest)
            layout.paint(page, plotter, device)
