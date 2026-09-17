"""Year planner book — cover → annual → favorites → my 100 → checkoff → quarters → months+habits → weeks → days+notes → review → projects index/dests → meetings → tasks.

``spec.favorites_pages``, ``spec.my_100``, and ``spec.checkoff_365`` (all
default off) insert after annual and before quarters; when on, favorites
then my 100 then checkoff.
"""

from parch.books.protocol import plot_pages
from parch.calendar import months_touching_weeks
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import (
    AnnualSection,
    Checkoff365Section,
    CoverSection,
    DailyNotesSection,
    DailySection,
    FavoritesSection,
    HabitSection,
    MeetingSection,
    MonthSection,
    My100Section,
    Page,
    ProjectsSection,
    QuarterSection,
    ReviewSection,
    TasksSection,
    WeeklySection,
)
from parch.spec import Spec


class YearPlanner:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        daily = DailySection(spec)
        notes = DailyNotesSection(spec)
        weekly = WeeklySection(spec)
        month = MonthSection(spec)
        habits = HabitSection(spec)
        built = [
            *CoverSection(spec).pages(),
            *AnnualSection(spec).pages(),
            *FavoritesSection(spec).pages(),
            *My100Section(spec).pages(),
            *Checkoff365Section(spec).pages(),
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
        built.extend(ReviewSection(spec).pages())
        built.extend(ProjectsSection(spec).pages())
        built.extend(MeetingSection(spec).pages())
        built.extend(TasksSection(spec).pages())
        return built

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=spec.outline,
        )
