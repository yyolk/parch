from parch.calendar import month_touching_weeks
from parch.components import FavoritesPage
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class FavoritesSection:
    """Optional year-scoped rankings page. After annual; default empty."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        if spec.favorites_pages < 1:
            return []
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        dest = spec.favorites_dest
        return [
            Page(
                dest=dest,
                title="Favorites",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(FavoritesPage(year=spec.year),),
            )
        ]
