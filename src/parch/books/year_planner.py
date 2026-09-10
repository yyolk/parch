"""Year planner book — cover → annual → projects board → index → project leaves → quarters → months+habits → weeks → days."""

from parch.calendar import months_touching_weeks
from parch.devices import get_device
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import (
    AnnualSection,
    CoverSection,
    DailyNotesSection,
    DailySection,
    HabitSection,
    MonthSection,
    Page,
    ProjectsSection,
    QuarterSection,
    WeeklySection,
)
from parch.spec import Spec


class YearPlanner:
    def pages(self, spec: Spec) -> list[Page]:
        daily = DailySection(spec)
        notes = DailyNotesSection(spec)
        weekly = WeeklySection(spec)
        month = MonthSection(spec)
        habits = HabitSection(spec)
        built = [
            *CoverSection(spec).pages(),
            *AnnualSection(spec).pages(),
            *ProjectsSection(spec).pages(),
            *QuarterSection(spec).pages(),
        ]
        for number in spec.months:
            built.extend(month.pages_for(number))
            built.extend(habits.pages_for(number))
        for week in months_touching_weeks(spec.year, spec.months, spec.weekday_start):
            built.extend(weekly.pages_for(week))
            for day in week:
                if not spec.presses_day(day):
                    continue
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
