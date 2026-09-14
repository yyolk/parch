"""Year planner book — cover → annual → projects index/dests → meetings → tasks → review → quarters → months+habits → weeks → days."""

from parch.books.outline import OutlineEntry, outline_for
from parch.books.protocol import plot_pages
from parch.calendar import months_touching_weeks
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import (
    AnnualSection,
    CoverSection,
    DailyNotesSection,
    DailySection,
    HabitSection,
    MeetingSection,
    MonthSection,
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
            *ProjectsSection(spec).pages(),
            *MeetingSection(spec).pages(),
            *TasksSection(spec).pages(),
            *ReviewSection(spec).pages(),
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

    def outline_entries(self, spec: Spec) -> list[OutlineEntry]:
        weeks = months_touching_weeks(spec.year, spec.months, spec.weekday_start)
        first_week = weeks[0]
        first_day = next(day for day in first_week if spec.presses_day(day))
        return [
            OutlineEntry("Annual", spec.year_dest),
            OutlineEntry("Projects", spec.projects_index_dest),
            OutlineEntry("Meetings", spec.meetings_index_dest),
            OutlineEntry("Tasks", spec.tasks_index_dest),
            OutlineEntry("Review", spec.review_index_dest),
            OutlineEntry("Quarters", spec.dest_for_quarter(spec.pressed_quarters()[0])),
            OutlineEntry("Months", spec.dest_for_month(spec.months[0])),
            OutlineEntry("Weeks", spec.dest_for_week(first_week[0])),
            OutlineEntry("Days", spec.dest_for_day(first_day)),
        ]

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=outline_for(self, spec),
        )
