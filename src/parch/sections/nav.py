"""Planner strip dests. Layout remaps these into Cover · Mon · Week · Day · Notes.

WEEK dest: daily/notes → ISO week of that day; week page → self; month → first
ISO week that touches the month.

DAY dest: daily/notes → that day; week → first in-month day of the week;
month → spec.date landing.
"""

from datetime import date

from parch.sections.page import NavItem
from parch.spec import Spec


def planner_nav(spec: Spec, *, week_dest: str, day: date | None = None) -> tuple[NavItem, ...]:
    landing = day or spec.date
    items = [
        NavItem("Cover", spec.cover_dest),
        NavItem("Mon", spec.month_dest),
        NavItem("Week", week_dest),
        NavItem("Day", spec.dest_for_day(landing)),
    ]
    if spec.notes_pages > 0:
        items.append(NavItem("Notes", spec.dest_for_notes(landing, 1)))
    return tuple(items)
