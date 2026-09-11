"""Per-section StylePacks — named TypeInk fields, no role enum.

Each section declares only the inks it paints. ``PlannerLayout`` builds the
set from a ``JostRamp`` / catalog factory and passes the pack in. Painters
read ``pack.body`` / ``pack.title`` / … — never ``face`` / ``bold`` and never
a global role table.

``BaseChrome`` (header + nav) is composed into every well pack.
"""

from dataclasses import dataclass
from typing import Protocol

from parch.fonts.catalog import FontCatalog, TypeWeight
from parch.fonts.ramp import TypeInk


@dataclass(frozen=True, slots=True)
class NavPack:
    """Bottom strip — idle chip vs lit chip."""

    idle: TypeInk
    active: TypeInk


@dataclass(frozen=True, slots=True)
class BaseChrome:
    """Header slab + nav. Composed into well-section packs."""

    title: TypeInk
    meta: TypeInk
    nav: NavPack


@dataclass(frozen=True, slots=True)
class CoverPack:
    year: TypeInk
    brow: TypeInk
    specs: TypeInk


@dataclass(frozen=True, slots=True)
class MiniMonthPack:
    """Year-density calendar thumbnail (annual / daily / quarter)."""

    month: TypeInk
    month_on: TypeInk
    weekday: TypeInk
    day: TypeInk
    day_on: TypeInk
    day_mark: TypeInk


@dataclass(frozen=True, slots=True)
class AnnualPack:
    chrome: BaseChrome
    mini: MiniMonthPack


@dataclass(frozen=True, slots=True)
class MonthPack:
    chrome: BaseChrome
    weekday: TypeInk
    week: TypeInk
    day: TypeInk


@dataclass(frozen=True, slots=True)
class WeekPack:
    chrome: BaseChrome
    weekday: TypeInk
    day: TypeInk
    month: TypeInk


@dataclass(frozen=True, slots=True)
class DailyPack:
    chrome: BaseChrome
    label: TypeInk
    hour: TypeInk
    mini: MiniMonthPack


@dataclass(frozen=True, slots=True)
class ProjectsPack:
    chrome: BaseChrome
    stub: TypeInk
    mark: TypeInk
    status: TypeInk


@dataclass(frozen=True, slots=True)
class TasksPack:
    chrome: BaseChrome
    band: TypeInk
    week: TypeInk
    range: TypeInk
    label: TypeInk


@dataclass(frozen=True, slots=True)
class ReviewPack:
    chrome: BaseChrome
    band: TypeInk
    chip: TypeInk
    weekday: TypeInk
    day: TypeInk


@dataclass(frozen=True, slots=True)
class HabitPack:
    chrome: BaseChrome
    day: TypeInk
    weekday: TypeInk
    label: TypeInk
    head_day: TypeInk
    head_weekday: TypeInk


@dataclass(frozen=True, slots=True)
class MeetingPack:
    chrome: BaseChrome
    label: TypeInk
    stub: TypeInk
    cue: TypeInk


@dataclass(frozen=True, slots=True)
class QuarterPack:
    chrome: BaseChrome
    mini: MiniMonthPack
    label: TypeInk


@dataclass(frozen=True, slots=True)
class PlannerPacks:
    """One frozen pack per section. Built once from the Jost factory."""

    cover: CoverPack
    annual: AnnualPack
    month: MonthPack
    week: WeekPack
    daily: DailyPack
    projects: ProjectsPack
    tasks: TasksPack
    review: ReviewPack
    habit: HabitPack
    meeting: MeetingPack
    quarter: QuarterPack


class TypeRamp(Protocol):
    """Catalog + StylePack factory. Explicit object — no ambient lookup."""

    catalog: FontCatalog

    def packs(self) -> PlannerPacks:
        """Build the frozen per-section packs."""
        ...


def _jost(weight: TypeWeight, size: float) -> TypeInk:
    return TypeInk(family="jost", weight=weight, size=size)


def build_jost_packs(catalog: FontCatalog) -> PlannerPacks:
    """Resolve every pack field through the Jost catalog (raises if a cut is missing)."""

    def ink(weight: TypeWeight, size: float) -> TypeInk:
        catalog.path("jost", weight)
        return _jost(weight, size)

    nav = NavPack(idle=ink("book", 7.6), active=ink("bold", 7.6))
    chrome = BaseChrome(title=ink("medium", 11), meta=ink("book", 7.4), nav=nav)
    mini = MiniMonthPack(
        month=ink("book", 6.4),
        month_on=ink("bold", 6.4),
        weekday=ink("book", 4.3),
        day=ink("book", 5.3),
        day_on=ink("bold", 5.3),
        day_mark=ink("bold", 5.3),
    )
    label = ink("book", 6.4)
    return PlannerPacks(
        cover=CoverPack(
            year=ink("heavy", 42),
            brow=ink("medium", 10),
            specs=ink("book", 8.2),
        ),
        annual=AnnualPack(chrome=chrome, mini=mini),
        month=MonthPack(
            chrome=chrome,
            weekday=ink("book", 6.6),
            week=ink("book", 5.8),
            day=ink("bold", 8.5),
        ),
        week=WeekPack(
            chrome=chrome,
            weekday=ink("book", 6.6),
            day=ink("bold", 11),
            month=ink("book", 6.6),
        ),
        daily=DailyPack(chrome=chrome, label=label, hour=ink("book", 7), mini=mini),
        projects=ProjectsPack(
            chrome=chrome,
            stub=ink("medium", 6.6),
            mark=ink("book", 5.2),
            status=ink("book", 5.4),
        ),
        tasks=TasksPack(
            chrome=chrome,
            band=ink("bold", 6.4),
            week=ink("medium", 7.2),
            range=ink("book", 6.2),
            label=label,
        ),
        review=ReviewPack(
            chrome=chrome,
            band=ink("bold", 6.2),
            chip=ink("medium", 7.0),
            weekday=ink("book", 5.6),
            day=ink("bold", 9.2),
        ),
        habit=HabitPack(
            chrome=chrome,
            day=ink("book", 4.4),
            weekday=ink("book", 4.4),
            label=ink("book", 5.8),
            head_day=ink("book", 3.5),
            head_weekday=ink("book", 3.3),
        ),
        meeting=MeetingPack(
            chrome=chrome,
            label=label,
            stub=ink("medium", 6.2),
            cue=ink("book", 5.8),
        ),
        quarter=QuarterPack(chrome=chrome, mini=mini, label=label),
    )


def default_packs() -> PlannerPacks:
    """Jost default — tests that paint a well without a pack still resolve."""
    from parch.fonts.ramp import JostRamp

    return JostRamp().packs()
