"""Engineering / computation pad — duplex sheets as the unit of identity (E6).

``sheet()`` builds one ``PadSheet`` whose ``front`` / ``back`` share a sheet
number. The section flattens those tuples; pairing does not live on page
kinds or a face flag.
"""

from dataclasses import dataclass

from parch.calendar import month_touching_weeks
from parch.components import PadBlank, PadGrid
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


def sheet_label(number: int, of: int) -> str:
    """Shared header identity for both faces of one sheet."""
    return f"Sheet {number} of {of}"


@dataclass(frozen=True, slots=True)
class PadSheet:
    """One physical sheet: front + back pages share ``number`` / ``of``."""

    number: int
    of: int
    front: Page
    back: Page

    def pages(self) -> tuple[Page, Page]:
        return self.front, self.back


def sheet(spec: Spec, number: int, of: int) -> PadSheet:
    """Build one duplex unit. Front and back keep the same sheet identity."""
    if of < 1:
        raise ValueError(f"sheet of must be >= 1, not {of}")
    if not 1 <= number <= of:
        raise ValueError(f"sheet number {number} is not in 1..{of}")
    first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
    nav = planner_nav(
        spec,
        week_dest=spec.dest_for_week(first[0]),
        pad_dest=spec.dest_for_pad(number),
    )
    label = sheet_label(number, of)
    front = Page(
        dest=spec.dest_for_pad(number),
        kind="pad_front",
        title=label,
        nav=nav,
        components=(PadBlank(number=number, of=of, year=spec.year),),
    )
    back = Page(
        dest=spec.dest_for_pad(number, back=True),
        kind="pad_back",
        title=label,
        nav=nav,
        components=(PadGrid(number=number, of=of, year=spec.year),),
    )
    return PadSheet(number=number, of=of, front=front, back=back)


class EngineeringPadSection:
    """Flatten ``PadSheet`` tuples into the book page list."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def sheets(self) -> list[PadSheet]:
        of = self.spec.pad_sheets
        return [sheet(self.spec, number, of) for number in range(1, of + 1)]

    def pages(self) -> list[Page]:
        built: list[Page] = []
        for unit in self.sheets():
            built.extend(unit.pages())
        return built
