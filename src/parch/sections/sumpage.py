"""Closed page sum: a kind tag plus that kind's payload."""

from dataclasses import dataclass
from datetime import date
from typing import Literal, assert_never

from parch.components import AnnualGrid, CoverTitle, DotGridPad, MonthGrid, WeekStrip
from parch.sections.page import NavItem, Page


@dataclass(frozen=True, slots=True)
class Chrome:
    """Planner header and strip. Pad payloads do not carry this."""

    title: str
    nav: tuple[NavItem, ...]


@dataclass(frozen=True, slots=True)
class CoverPayload:
    """Cover face. No strip and no sheet count."""

    year: int
    eyebrow: str
    cta_label: str
    cta_dest: str
    specs_lead: str
    display_title: str | None = None


@dataclass(frozen=True, slots=True)
class AnnualWell:
    """Annual well identity."""

    year: int
    quarter_dest: str | None


@dataclass(frozen=True, slots=True)
class MonthWell:
    """Month well identity."""

    year: int
    month: int
    quarter_dest: str | None


@dataclass(frozen=True, slots=True)
class WeeklyWell:
    """Week well identity."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date


@dataclass(frozen=True, slots=True)
class AnnualPayload:
    """Chrome family payload for an annual page."""

    chrome: Chrome
    well: AnnualWell


@dataclass(frozen=True, slots=True)
class MonthPayload:
    """Chrome family payload for a month page."""

    chrome: Chrome
    well: MonthWell


@dataclass(frozen=True, slots=True)
class WeeklyPayload:
    """Chrome family payload for a week page."""

    chrome: Chrome
    well: WeeklyWell


@dataclass(frozen=True, slots=True)
class DotgridPayload:
    """Pad family payload. One full-bleed sheet, no title and no nav."""

    sheet: int
    sheets: int


@dataclass(frozen=True, slots=True)
class CoverPage:
    """Cover variant."""

    kind: Literal["cover"]
    dest: str
    payload: CoverPayload


@dataclass(frozen=True, slots=True)
class AnnualPage:
    """Annual variant. Payload is the chrome family."""

    kind: Literal["annual"]
    dest: str
    payload: AnnualPayload


@dataclass(frozen=True, slots=True)
class MonthPage:
    """Month variant. Payload is the chrome family."""

    kind: Literal["month"]
    dest: str
    payload: MonthPayload


@dataclass(frozen=True, slots=True)
class WeeklyPage:
    """Week variant. Payload is the chrome family."""

    kind: Literal["weekly"]
    dest: str
    payload: WeeklyPayload


@dataclass(frozen=True, slots=True)
class DotgridPage:
    """Dot-grid variant. Payload is the pad family."""

    kind: Literal["dotgrid"]
    dest: str
    payload: DotgridPayload


type PlannerPage = AnnualPage | MonthPage | WeeklyPage
type PadPage = DotgridPage
type SumPage = CoverPage | AnnualPage | MonthPage | WeeklyPage | DotgridPage


@dataclass(frozen=True, slots=True)
class CoverSeat:
    """Where a cover page sits."""

    dest: str
    year: int
    cta_dest: str


@dataclass(frozen=True, slots=True)
class ChromeSeat:
    """Where a planner page sits."""

    dest: str
    title: str
    nav: int
    mark: str


@dataclass(frozen=True, slots=True)
class PadSeat:
    """Where a pad page sits."""

    dest: str
    sheet: int
    sheets: int


type Seat = CoverSeat | ChromeSeat | PadSeat


def planner_title(page: PlannerPage) -> str:
    """Chrome-family pages share a frame. Pad pages have no title slot."""

    match page.kind:
        case "annual" | "month" | "weekly":
            return page.payload.chrome.title
        case _ as unreachable:
            assert_never(unreachable)


def pad_sheets(page: PadPage) -> int:
    """Pad-family pages expose a sheet count. Chrome pages do not."""

    match page.kind:
        case "dotgrid":
            return page.payload.sheets
        case _ as unreachable:
            assert_never(unreachable)


def seat(page: SumPage) -> Seat:
    """Dispatch on kind. Each arm reads only that variant's payload."""

    match page.kind:
        case "cover":
            body = page.payload
            return CoverSeat(page.dest, body.year, body.cta_dest)
        case "annual":
            return ChromeSeat(
                page.dest,
                page.payload.chrome.title,
                len(page.payload.chrome.nav),
                f"Year {page.payload.well.year}",
            )
        case "month":
            return ChromeSeat(
                page.dest,
                page.payload.chrome.title,
                len(page.payload.chrome.nav),
                f"Mon {page.payload.well.month}",
            )
        case "weekly":
            return ChromeSeat(
                page.dest,
                page.payload.chrome.title,
                len(page.payload.chrome.nav),
                f"Week {page.payload.well.iso_week:02d}",
            )
        case "dotgrid":
            face = page.payload
            return PadSeat(page.dest, face.sheet, face.sheets)
        case _ as unreachable:
            assert_never(unreachable)


def lift(page: Page) -> SumPage:
    """Project a demo kind off its Component tuple. Other kinds stay on Page."""

    match page.kind:
        case "cover":
            title = _only(page, CoverTitle)
            return CoverPage(
                kind="cover",
                dest=page.dest,
                payload=CoverPayload(
                    year=title.year,
                    eyebrow=title.eyebrow,
                    cta_label=title.cta_label,
                    cta_dest=title.cta_dest,
                    specs_lead=title.specs_lead,
                    display_title=title.display_title,
                ),
            )
        case "annual":
            grid = _only(page, AnnualGrid)
            return AnnualPage(
                kind="annual",
                dest=page.dest,
                payload=AnnualPayload(
                    chrome=Chrome(title=page.title, nav=page.nav),
                    well=AnnualWell(year=grid.year, quarter_dest=grid.quarter_dest),
                ),
            )
        case "month":
            grid = _only(page, MonthGrid)
            return MonthPage(
                kind="month",
                dest=page.dest,
                payload=MonthPayload(
                    chrome=Chrome(title=page.title, nav=page.nav),
                    well=MonthWell(
                        year=grid.year,
                        month=grid.month,
                        quarter_dest=grid.quarter_dest,
                    ),
                ),
            )
        case "weekly":
            strip = _only(page, WeekStrip)
            return WeeklyPage(
                kind="weekly",
                dest=page.dest,
                payload=WeeklyPayload(
                    chrome=Chrome(title=page.title, nav=page.nav),
                    well=WeeklyWell(
                        iso_year=strip.iso_year,
                        iso_week=strip.iso_week,
                        monday=strip.monday,
                        sunday=strip.sunday,
                    ),
                ),
            )
        case "dotgrid":
            pad = _only(page, DotGridPad)
            return DotgridPage(
                kind="dotgrid",
                dest=page.dest,
                payload=DotgridPayload(sheet=pad.sheet, sheets=pad.sheets),
            )
        case _:
            raise ValueError(f"sum slice does not include {page.kind}")


def _only[T](page: Page, typ: type[T]) -> T:
    found = [item for item in page.components if isinstance(item, typ)]
    if len(found) != 1:
        raise TypeError(f"{page.kind} page expected one {typ.__name__}")
    return found[0]
