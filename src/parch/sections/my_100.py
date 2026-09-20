from parch.calendar import month_touching_weeks
from parch.components import My100Page
from parch.devices import get_device
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class My100Section:
    """``paint_my_100`` numbered write-in list.

    YearPlanner inserts these after annual and before quarters when
    ``Spec.my_100`` is on. Off (the default) emits nothing.
    """

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        if not spec.my_100:
            return []
        # Late import: painters → sections.page loads this package.
        from parch.layouts.planner.painters import (
            my_100_page_count,
            my_100_page_numbers,
            well_rect,
        )

        well = well_rect(get_device(spec.device, top_clearance=spec.top_clearance))
        pages_n = my_100_page_count(well)
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        nav = planner_nav(spec, week_dest=spec.dest_for_week(first[0]))
        landing = spec.my_100_dest
        built: list[Page] = []
        for page in range(1, pages_n + 1):
            dest = spec.dest_for_my_100(page)
            built.append(
                Page(
                    dest=dest,
                    kind="my_100",
                    title="My 100",
                    nav=nav,
                    components=(
                        My100Page(
                            year=spec.year,
                            dest=dest,
                            page=page,
                            pages=pages_n,
                            numbers=my_100_page_numbers(well, page),
                            index_dest=landing,
                        ),
                    ),
                )
            )
        return built
