from datetime import date, timedelta

from parch.calendar import WEEKDAY_LABELS, iso_monday, month_week_bands, quarter_of
from parch.components import ReviewDay, ReviewIndex, ReviewWeek, ReviewWeekPage
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ReviewSection:
    """Exploratory Review dest E + thin quarter indexes. Not in YearPlanner."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        by_quarter: dict[int, list[ReviewWeek]] = {}
        for month, weeks in month_week_bands(spec.year, spec.months, spec.weekday_start):
            quarter = quarter_of(month)
            for week in weeks:
                by_quarter.setdefault(quarter, []).append(self._review_week(week))
        for quarter in spec.pressed_quarters():
            weeks = tuple(by_quarter.get(quarter, ()))
            if not weeks:
                continue
            first = weeks[0]
            landing = self._landing(first.monday)
            index_dest = spec.dest_for_reviews_index(quarter)
            built.append(
                Page(
                    dest=index_dest,
                    kind="reviews_index",
                    title="Review",
                    nav=planner_nav(
                        spec,
                        week_dest=spec.dest_for_week(first.monday),
                        day=landing,
                        month=landing.month,
                        rev_dest=index_dest,
                    ),
                    components=(
                        ReviewIndex(
                            year=spec.year,
                            dest=index_dest,
                            quarter=quarter,
                            weeks=weeks,
                        ),
                    ),
                )
            )
            for week in weeks:
                built.append(self._dest_page(week, index_dest))
        return built

    def _review_week(self, week: list[date]) -> ReviewWeek:
        spec = self.spec
        monday = next((day for day in week if day.weekday() == 0), iso_monday(week[0]))
        iso = monday.isocalendar()
        return ReviewWeek(
            iso_year=iso.year,
            iso_week=iso.week,
            monday=monday,
            sunday=monday + timedelta(days=6),
            dest=spec.dest_for_review(monday),
        )

    def _dest_page(self, week: ReviewWeek, index_dest: str) -> Page:
        spec = self.spec
        landing = self._landing(week.monday)
        days = tuple(
            ReviewDay(
                day=day,
                weekday_label=WEEKDAY_LABELS[day.weekday()],
                dest=spec.dest_for_day(day) if spec.presses_day(day) else None,
            )
            for day in (week.monday + timedelta(days=offset) for offset in range(7))
        )
        return Page(
            dest=week.dest,
            kind="review",
            title="Review",
            nav=planner_nav(
                spec,
                week_dest=spec.dest_for_week(week.monday),
                day=landing,
                month=landing.month,
                rev_dest=index_dest,
            ),
            components=(
                ReviewWeekPage(
                    year=spec.year,
                    iso_year=week.iso_year,
                    iso_week=week.iso_week,
                    monday=week.monday,
                    sunday=week.sunday,
                    days=days,
                    index_dest=index_dest,
                ),
            ),
        )

    def _landing(self, monday: date) -> date:
        spec = self.spec
        week = [monday + timedelta(days=offset) for offset in range(7)]
        pressed = [day for day in week if spec.presses_day(day)]
        return pressed[0] if pressed else monday
