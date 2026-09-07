"""Scribe-family Hyperpaper nav exploration. Nomad stays on mos_strip."""

from parch.calendar.dated_note import DatedNote
from parch.calendar.week import Week
from parch.devices import is_scribe_family

# Gridwright lock tokens. Header owns air; toolbar stays none / 0mm.
NAV_HEADER_HEIGHT = "10mm"
NAV_HEADER_AIR = "5mm"
RAIL_PAD = "4mm"

RAIL_SKIP = frozenset({"cover", "index", "colophon"})

# Enabled sections → rail labels (Hyperpaper Notes/Projects/Meetings style).
RAIL_LABELS = {
    "annual": "Calendar",
    "quarterly": "Quarters",
    "monthly": "Months",
    "weekly": "Weeks",
    "daily": "Days",
    "daily_notes": "Notes",
    "projects": "Projects",
    "habits": "Habits",
    "review": "Review",
    "tasks": "Tasks",
    "meetings": "Meetings",
}

# Contents / index human labels stay shared with the rail where they overlap.
INDEX_LABELS = {
    **{name: label for name, label in RAIL_LABELS.items() if name != "daily_notes"},
    "colophon": "About this notebook",
}

INDEX_SKIP = frozenset({"cover", "index", "daily_notes"})


def scribe_hyperpaper_nav(configurator) -> bool:
    """Device-gated explor path. Missing device keeps the Nomad MOS layout."""
    device = configurator.dig("device") if configurator is not None else None
    if device is None:
        return False
    return is_scribe_family(str(device))


def section_dest_id(name: str, configurator) -> str:
    """First-page dest for an enabled section name."""
    if name == "annual":
        return "annual"
    if name == "quarterly":
        return configurator.start_date().quarter().id
    if name == "monthly":
        return configurator.start_date().month().id
    if name == "weekly":
        first = configurator.start_date().beginning_of_month().beginning_of_week()
        return Week(weekday_start=configurator.weekday_start(), day=first).id
    if name == "daily":
        return configurator.start_date().id
    if name == "daily_notes":
        day = configurator.start_date()
        return DatedNote(weekday_start=day.weekday_start, day=day, page=1).id
    return name


def rail_section_names(configurator) -> list[str]:
    """Enabled section names that belong on the Scribe rail."""
    names: list[str] = []
    for section in configurator.enabled_sections():
        name = str(section["name"])
        if name not in RAIL_SKIP and name in RAIL_LABELS:
            names.append(name)
    return names


def section_name_for_page_id(page_id: str | None) -> str | None:
    """Map a live page dest onto the rail section that should highlight."""
    if not page_id:
        return None
    if page_id == "annual":
        return "annual"
    if page_id.startswith("quarter-"):
        return "quarterly"
    if page_id.startswith("month-"):
        return "monthly"
    if page_id.startswith("daily-note-"):
        return "daily_notes"
    if page_id.startswith("habits"):
        return "habits"
    if page_id == "projects" or page_id.startswith("project"):
        return "projects"
    if page_id == "meetings" or page_id.startswith("meeting"):
        return "meetings"
    if page_id.startswith("review"):
        return "review"
    if page_id.startswith("tasks"):
        return "tasks"
    if len(page_id) >= 6 and page_id[4] == "W" and page_id[0].isdigit():
        return "weekly"
    if len(page_id) == 10 and page_id[4] == "-" and page_id[7] == "-":
        return "daily"
    return None
