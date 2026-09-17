"""Optional Hobonichi-style year lists — Favorites, My 100, 365 Days.

Stubs so a press includes dests. Sibling exploratories fill the painters.
Each section is empty when its Spec flag is off (defaults off).
"""

from parch.calendar import month_touching_weeks
from parch.components import Notes
from parch.sections.nav import planner_nav
from parch.sections.page import NavItem, Page, PageKind
from parch.spec import Spec


def _list_nav(spec: Spec) -> tuple[NavItem, ...]:
    first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
    return planner_nav(spec, week_dest=spec.dest_for_week(first[0]))


def _stub(spec: Spec, *, dest: str, kind: PageKind, title: str) -> Page:
    return Page(
        dest=dest,
        kind=kind,
        title=title,
        nav=_list_nav(spec),
        components=(Notes(label="placeholder"),),
    )


class FavoritesSection:
    """Year Favorites ranking tables. Stub: title + ruled placeholder."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        if not spec.lists_favorites:
            return []
        return [
            _stub(spec, dest=spec.favorites_dest, kind="favorites", title="Favorites")
        ]


class My100Section:
    """My 100 numbered checklist. Stub: title + ruled placeholder."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        if not spec.lists_my_100:
            return []
        return [_stub(spec, dest=spec.my_100_dest, kind="my_100", title="My 100")]


class Days365Section:
    """365 Days check-off sheet. Stub: title + ruled placeholder."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        if not spec.lists_days_365:
            return []
        return [_stub(spec, dest=spec.days_365_dest, kind="days_365", title="365 Days")]
