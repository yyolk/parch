from datetime import date, timedelta

from parch.calendar import MONTH_NAMES, iso_monday, month_week_bands, quarter_of
from parch.components import ReviewWeek, ReviewsIndex, ReviewsMonthColumn, ReviewWeekPage
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ReviewSection:
    """Exploratory Reviews index A + weekly dest stubs. Month columns; not in YearPlanner."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        by_quarter: dict[int, list[ReviewsMonthColumn]] = {}
        for column in self._columns(spec.months):
            by_quarter.setdefault(quarter_of(column.month), []).append(column)
        for quarter in spec.pressed_quarters():
            columns = tuple(by_quarter.get(quarter, ()))
            if not columns:
                continue
            first_week = columns[0].weeks[0]
            landing = self._landing(first_week.monday)
            index_dest = spec.dest_for_reviews_index(quarter)
            built.append(
                Page(
                    dest=index_dest,
                    kind="reviews_index",
                    title="Reviews",
                    nav=planner_nav(
                        spec,
                        week_dest=spec.dest_for_week(first_week.monday),
                        day=landing,
                        month=landing.month,
                        review_dest=index_dest,
                    ),
                    components=(
                        ReviewsIndex(
                            year=spec.year,
                            dest=index_dest,
                            quarter=quarter,
                            columns=columns,
                        ),
                    ),
                )
            )
            for column in columns:
                for week in column.weeks:
                    built.append(self._dest_page(week, index_dest))
        return built

    def _columns(self, months: tuple[int, ...]) -> tuple[ReviewsMonthColumn, ...]:
        spec = self.spec
        columns: list[ReviewsMonthColumn] = []
        for month, weeks in month_week_bands(spec.year, months, spec.weekday_start):
            chips = tuple(self._review_week(week) for week in weeks)
            columns.append(
                ReviewsMonthColumn(month=month, name=MONTH_NAMES[month - 1], weeks=chips)
            )
        return tuple(columns)

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
        return Page(
            dest=week.dest,
            kind="review",
            title="Review",
            nav=planner_nav(
                spec,
                week_dest=spec.dest_for_week(week.monday),
                day=landing,
                month=landing.month,
                review_dest=index_dest,
            ),
            components=(
                ReviewWeekPage(
                    year=spec.year,
                    iso_year=week.iso_year,
                    iso_week=week.iso_week,
                    monday=week.monday,
                    sunday=week.sunday,
                    index_dest=index_dest,
                ),
            ),
        )

    def _landing(self, monday: date) -> date:
        spec = self.spec
        week = [monday + timedelta(days=offset) for offset in range(7)]
        pressed = [day for day in week if spec.presses_day(day)]
        return pressed[0] if pressed else monday
