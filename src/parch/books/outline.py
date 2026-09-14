"""Reader outline (bookmarks) from existing page dests. No printed TOC."""

from collections.abc import Iterable

from parch.calendar import iso_monday, month_name, month_week_bands, quarter_of
from parch.plotter.protocol import Plotter
from parch.sections.page import Page
from parch.spec import Spec

# Depth stops at Week (level 3 under Annual / Quarter / Month). A full
# year of Days (365) plus notes wells drowns the reader sidebar; weeks
# still show a four-level tree and only bookmark dests that already exist.


def outline_tree(spec: Spec, dests: set[str]) -> list[tuple[str, str, int]]:
    """``(title, dest, level)`` rows. Only dests in ``dests``; never cover."""
    if spec.book == "engineering-notebook":
        return _hub(dests, "Engineering", spec.dest_for_engineering_pad(1, "front"))
    if spec.book == "projects-notebook":
        return _hub(dests, "Projects", spec.projects_index_dest)
    return _year_planner_tree(spec, dests)


def apply_outline(spec: Spec, plotter: Plotter, pages: Iterable[Page]) -> None:
    """Bookmark existing dests when ``spec.outline``; no-op when disabled."""
    if not spec.outline:
        return
    dests = {page.dest for page in pages if page.kind != "cover"}
    for title, dest, level in outline_tree(spec, dests):
        plotter.outline(title, dest, level=level)


def _hub(dests: set[str], title: str, dest: str) -> list[tuple[str, str, int]]:
    if dest not in dests:
        return []
    return [(title, dest, 0)]


def _year_planner_tree(spec: Spec, dests: set[str]) -> list[tuple[str, str, int]]:
    rows: list[tuple[str, str, int]] = []
    if spec.year_dest in dests:
        rows.append(("Annual", spec.year_dest, 0))
    bands = dict(month_week_bands(spec.year, spec.months, spec.weekday_start))
    for quarter in spec.pressed_quarters():
        qdest = spec.dest_for_quarter(quarter)
        if qdest not in dests:
            continue
        rows.append((f"Q{quarter}", qdest, 1))
        for month in spec.months:
            if quarter_of(month) != quarter:
                continue
            mdest = spec.dest_for_month(month)
            if mdest not in dests:
                continue
            rows.append((month_name(month), mdest, 2))
            hdest = spec.dest_for_habits(month)
            if hdest in dests:
                rows.append(("Habits", hdest, 3))
            for week in bands.get(month, ()):
                monday = next(
                    (day for day in week if day.weekday() == 0), iso_monday(week[0])
                )
                wdest = spec.dest_for_week(monday)
                if wdest not in dests:
                    continue
                rows.append((f"Week {monday.isocalendar().week:02d}", wdest, 3))
    for title, dest in (
        ("Projects", spec.projects_index_dest),
        ("Meetings", spec.meetings_index_dest),
        ("Tasks", spec.tasks_index_dest),
        ("Review", spec.review_index_dest),
    ):
        rows.extend(_hub(dests, title, dest))
    return rows
