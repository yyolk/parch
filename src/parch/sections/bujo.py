"""Bullet journal sections — key, index, future log, monthly, rapid-log, collections."""

import calendar
from datetime import date

from parch.calendar import WEEKDAY_LABELS, month_days, month_name
from parch.components import (
    BujoIndex,
    BujoIndexRow,
    BujoKey,
    BujoKeySymbol,
    CalendarDayRow,
    CollectionLeaf,
    FutureLogBand,
    FutureLogPage,
    HabitGrid,
    MonthlyCalendarList,
    MonthlyTaskWell,
    RapidLogPage,
)
from parch.components.bujo import FUTURE_LOG_MONTHS_PER_PAGE
from parch.sections.nav import bujo_nav
from parch.sections.page import Page, PageKind
from parch.spec import Spec

_KEY_SYMBOLS = (
    BujoKeySymbol(".", "task"),
    BujoKeySymbol("x", "complete", genesis=True),
    BujoKeySymbol(">", "migrated", genesis=True),
    BujoKeySymbol("<", "scheduled", genesis=True),
    BujoKeySymbol(".", "irrelevant", strike=True),
    BujoKeySymbol("\u2013", "note"),  # en dash — wider than hyphen-minus
    BujoKeySymbol("o", "event"),
    BujoKeySymbol("*", "priority"),
    BujoKeySymbol("!", "inspiration"),
)


def _index_rows(spec: Spec) -> tuple[BujoIndexRow, ...]:
    rows = [BujoIndexRow("Future log", spec.bujo_future_dest)]
    rows.extend(
        BujoIndexRow(month_name(month), spec.dest_for_month(month))
        for month in spec.months
    )
    rows.extend(
        BujoIndexRow(f"{number:02d}", spec.dest_for_bujo_collection(number))
        for number in range(1, spec.bujo_collections + 1)
    )
    return tuple(rows)


class BujoKeySection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        return [
            Page(
                dest=spec.bujo_key_dest,
                kind=PageKind.BUJO_KEY,
                title="Key",
                nav=bujo_nav(spec),
                components=(BujoKey(symbols=_KEY_SYMBOLS),),
            )
        ]


class BujoIndexSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        rows = _index_rows(spec)
        pages = spec.bujo_index_pages
        per = max(1, (len(rows) + pages - 1) // pages)
        built: list[Page] = []
        for page_i in range(1, pages + 1):
            start = (page_i - 1) * per
            dest = spec.dest_for_bujo_index(page_i)
            built.append(
                Page(
                    dest=dest,
                    kind=PageKind.BUJO_INDEX,
                    title="Index",
                    nav=bujo_nav(spec, index_dest=dest),
                    components=(
                        BujoIndex(
                            year=spec.year,
                            page=page_i,
                            pages=pages,
                            rows=rows[start : start + per],
                        ),
                    ),
                )
            )
        return built


class FutureLogSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        pages = spec.bujo_future_pages
        built: list[Page] = []
        for page_i in range(1, pages + 1):
            start = (page_i - 1) * FUTURE_LOG_MONTHS_PER_PAGE
            chunk = spec.months[start : start + FUTURE_LOG_MONTHS_PER_PAGE]
            dest = spec.dest_for_bujo_future(page_i)
            built.append(
                Page(
                    dest=dest,
                    kind=PageKind.FUTURE_LOG,
                    title="Future log",
                    nav=bujo_nav(spec, future_dest=dest),
                    components=(
                        FutureLogPage(
                            year=spec.year,
                            page=page_i,
                            pages=pages,
                            months=tuple(
                                FutureLogBand(
                                    month=month,
                                    name=month_name(month),
                                    dest=spec.dest_for_month(month),
                                )
                                for month in chunk
                            ),
                        ),
                    ),
                )
            )
        return built


class MonthlyLogSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages_for(self, month: int) -> list[Page]:
        spec = self.spec
        days = tuple(
            CalendarDayRow(
                day=moment.day,
                weekday=WEEKDAY_LABELS[moment.weekday()],
                dest=spec.dest_for_day(moment),
            )
            for moment in month_days(spec.year, month)
        )
        name = month_name(month)
        nav = bujo_nav(spec, month=month)
        return [
            Page(
                dest=spec.dest_for_month(month),
                kind=PageKind.MONTHLY_LOG,
                title=f"{name} {spec.year}",
                nav=nav,
                components=(
                    MonthlyCalendarList(
                        year=spec.year,
                        month=month,
                        month_name=name,
                        days=days,
                        tasks_dest=spec.dest_for_month_tasks(month),
                    ),
                ),
            ),
            Page(
                dest=spec.dest_for_month_tasks(month),
                kind=PageKind.MONTHLY_TASKS,
                title=f"Tasks · {name} {spec.year}",
                nav=nav,
                components=(
                    MonthlyTaskWell(
                        year=spec.year,
                        month=month,
                        month_name=name,
                        calendar_dest=spec.dest_for_month(month),
                    ),
                ),
            ),
        ]


class BujoHabitSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages_for(self, month: int) -> list[Page]:
        spec = self.spec
        days = calendar.monthrange(spec.year, month)[1]
        dests = tuple(
            spec.dest_for_day(date(spec.year, month, day)) for day in range(1, days + 1)
        )
        return [
            Page(
                dest=spec.dest_for_habits(month),
                kind=PageKind.HABITS,
                title=f"Habits · {month_name(month)} {spec.year}",
                nav=bujo_nav(spec, month=month),
                components=(
                    HabitGrid(
                        year=spec.year,
                        month=month,
                        month_name=month_name(month),
                        days=days,
                        rows=spec.habit_columns,
                        month_dest=spec.dest_for_month(month),
                        day_dests=dests,
                    ),
                ),
            )
        ]


class RapidLogSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages_for(self, month: int) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for moment in month_days(spec.year, month):
            dest = spec.dest_for_day(moment)
            weekday = WEEKDAY_LABELS[moment.weekday()]
            title = f"{weekday} {moment.day}"
            built.append(
                Page(
                    dest=dest,
                    kind=PageKind.RAPID_LOG,
                    title=title,
                    nav=bujo_nav(spec, day=moment, month=month),
                    components=(
                        RapidLogPage(
                            year=spec.year,
                            moment=moment,
                            title=title,
                            dest=dest,
                        ),
                    ),
                )
            )
        return built


class CollectionSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        return [
            Page(
                dest=spec.dest_for_bujo_collection(number),
                kind=PageKind.COLLECTION,
                title="Collections",
                nav=bujo_nav(
                    spec, collection_dest=spec.dest_for_bujo_collection(number)
                ),
                components=(
                    CollectionLeaf(
                        year=spec.year,
                        number=number,
                        index_dest=spec.bujo_index_dest,
                    ),
                ),
            )
            for number in range(1, spec.bujo_collections + 1)
        ]
