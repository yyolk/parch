"""Side-menu and heading navigation (port of LYP::Planners::MOS::Navigation)."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from parch.calendar import walk
from parch.calendar.month import Month
from parch.i18n import I18n
from parch.mos.components.months_menu import MonthsMenu
from parch.mos.components.quarters_menu import QuartersMenu
from parch.mos.configurator import Configurator
from parch.mos.contents_mark import INDEX_ID
from parch.mos.manifest import Manifest
from parch.mos.nomad_nav import (
    context_from_page_id,
    habits_month_id,
    index_listing_week,
    prev_next_week,
    review_week_id,
    strip_dest_id,
    strip_key_for_page_id,
    strip_keys,
    tasks_week_id,
    tempo_kind,
)
from parch.mos.scribe_nav import (
    RAIL_LABELS,
    rail_section_names,
    section_dest_id,
    section_name_for_page_id,
)


@dataclass(frozen=True)
class NavLink:
    id: str
    label: str


class Navigation:
    def __init__(self, i18n: I18n, manifest: Manifest, configurator: Configurator) -> None:
        self.i18n = i18n
        self.manifest = manifest
        self.configurator = configurator
        self.mos_layout = configurator.dig_bang("planner", "params", "mos_layout")
        self.heading = configurator.dig_bang("planner", "params", "heading")
        self.start_date = configurator.start_date()
        self.end_date = configurator.end_date()

    def year_month_items(self, month_link_id: Callable[[Month], str] | None = None) -> str:
        months = list(walk(self.start_date.month(), self.end_date.month()))
        if _v(self.mos_layout, "reverse_months_quarters_items"):
            months.reverse()
        return MonthsMenu(
            i18n=self.i18n,
            manifest=self.manifest,
            range=months,
            month_link_id=month_link_id,
        ).generate()

    def year_quarter_items(self) -> str:
        quarters = list(walk(self.start_date.quarter(), self.end_date.quarter()))
        if _v(self.mos_layout, "reverse_months_quarters_items"):
            quarters.reverse()
        return QuartersMenu(i18n=self.i18n, manifest=self.manifest, range=quarters).generate()

    def side_menu_cell(
        self,
        highlight_months: list[Any],
        highlight_quarters: list[Any],
        month_link_id: Callable[[Month], str] | None = None,
        show_quarters: bool = True,
    ) -> str:
        month_dests = self._highlight_dests(highlight_months, month_link_id)
        quarter_dests = self._highlight_dests(highlight_quarters)
        parts = [
            f"highlight-months: {_dest_array(month_dests)}",
            f"highlight-quarters: {_dest_array(quarter_dests)}",
        ]
        if month_link_id is not None:
            parts.insert(0, f"months: {self.year_month_items(month_link_id)}")
        if not show_quarters:
            parts.append("show-quarters: false")
        return f"mos_strip({', '.join(parts)})"

    def section_strip_items(self, page_id: str | None = None) -> str:
        """Typst array of (dest, key) for the Nomad Topband."""
        pairs: list[str] = []
        for key in strip_keys(self.configurator):
            dest = self.manifest.dest(strip_dest_id(key, page_id, self.configurator))
            pairs.append(f"({dest}, \"{key}\")")
        if not pairs:
            return "()"
        return f"({', '.join(pairs)},)"

    def section_strip_cell(self, page_id: str | None = None) -> str:
        active = strip_key_for_page_id(page_id)
        highlight = f"\"{active}\"" if active else "none"
        return f"section-strip({self.section_strip_items(page_id)}, active: {highlight})"

    def tempo_cell(self, page_id: str | None = None) -> str:
        """Contextual tempo bar, or ``none`` when the page has no tempo."""
        kind = tempo_kind(page_id)
        if kind is None:
            return "none"
        items = self._tempo_items(page_id, kind)
        if not items:
            return "none"
        return f"tempo-bar(({', '.join(items)},))"

    def _tempo_items(self, page_id: str | None, kind: str) -> list[str]:
        ctx = context_from_page_id(page_id, self.configurator)
        if kind == "daily":
            return self._daily_tempo(ctx)
        if kind == "weekly":
            return self._week_tempo(ctx.week, center_id=ctx.week.id if ctx.week else None)
        if kind == "tasks":
            week = ctx.tasks_week or ctx.week
            return self._week_tempo(
                week,
                center_id=index_listing_week(self.configurator, week, section="tasks")
                if week
                else None,
                prev_id=tasks_week_id(prev_next_week(week)[0]) if week else None,
                next_id=tasks_week_id(prev_next_week(week)[1]) if week else None,
            )
        if kind == "review":
            week = ctx.review_week or ctx.week
            return self._week_tempo(
                week,
                center_id=index_listing_week(self.configurator, week, section="review")
                if week
                else None,
                prev_id=review_week_id(prev_next_week(week)[0]) if week else None,
                next_id=review_week_id(prev_next_week(week)[1]) if week else None,
            )
        if kind == "monthly":
            return self._month_tempo(ctx.month, dest_id=ctx.month.id if ctx.month else None)
        if kind == "habits":
            if ctx.month is None:
                return []
            prev_m = (ctx.month.day + (-1)).month()
            next_m = (ctx.month.day.end_of_month() + 1).month()
            return self._month_tempo(
                ctx.month,
                dest_id=habits_month_id(ctx.month),
                prev_id=habits_month_id(prev_m),
                next_id=habits_month_id(next_m),
            )
        if kind == "quarterly":
            return self._quarter_tempo(ctx.quarter)
        return []

    def _daily_tempo(self, ctx) -> list[str]:
        chips: list[str] = []
        if ctx.week is not None:
            dest = self.manifest.dest(ctx.week.id)
            label = f"Wk{ctx.week.number}"
            chips.append(_tempo_chip(dest, label, False))
        if ctx.month is not None:
            dest = self.manifest.dest(ctx.month.id)
            label = self.i18n.t(f"months.short.{ctx.month.name}")
            chips.append(_tempo_chip(dest, label, True))
        if ctx.quarter is not None:
            dest = self.manifest.dest(ctx.quarter.id)
            label = f"{self.i18n.t('quarter.short')}{ctx.quarter.number}"
            chips.append(_tempo_chip(dest, label, False))
        return chips

    def _week_tempo(
        self,
        week,
        *,
        center_id: str | None,
        prev_id: str | None = None,
        next_id: str | None = None,
    ) -> list[str]:
        if week is None:
            return []
        prev, nxt = prev_next_week(week)
        if prev_id is None:
            prev_id = prev.id
        if next_id is None:
            next_id = nxt.id
        if center_id is None:
            center_id = week.id
        label = f"Wk{week.number}"
        return [
            _tempo_chip(self.manifest.dest(prev_id), "‹", False),
            _tempo_chip(self.manifest.dest(center_id), label, True),
            _tempo_chip(self.manifest.dest(next_id), "›", False),
        ]

    def _month_tempo(
        self,
        month,
        *,
        dest_id: str | None,
        prev_id: str | None = None,
        next_id: str | None = None,
    ) -> list[str]:
        if month is None:
            return []
        prev = month.day + (-1)
        nxt = month.day.end_of_month() + 1
        if prev_id is None:
            prev_id = prev.month().id
        if next_id is None:
            next_id = nxt.month().id
        if dest_id is None:
            dest_id = month.id
        label = self.i18n.t(f"months.short.{month.name}")
        return [
            _tempo_chip(self.manifest.dest(prev_id), "‹", False),
            _tempo_chip(self.manifest.dest(dest_id), label, True),
            _tempo_chip(self.manifest.dest(next_id), "›", False),
        ]

    def _quarter_tempo(self, quarter) -> list[str]:
        if quarter is None:
            return []
        prev = quarter.day + (-1)
        nxt = quarter.months()[-1].day.end_of_month() + 1
        label = f"{self.i18n.t('quarter.short')}{quarter.number}"
        return [
            _tempo_chip(self.manifest.dest(prev.quarter().id), "‹", False),
            _tempo_chip(self.manifest.dest(quarter.id), label, True),
            _tempo_chip(self.manifest.dest(nxt.quarter().id), "›", False),
        ]

    def section_rail_items(self) -> str:
        """Typst array of (dest, label) for the Scribe section rail."""
        pairs: list[str] = []
        for name in rail_section_names(self.configurator):
            dest = self.manifest.dest(section_dest_id(name, self.configurator))
            pairs.append(f"({dest}, [{RAIL_LABELS[name]}])")
        if not pairs:
            return "()"
        return f"({', '.join(pairs)},)"

    def section_rail_cell(self, page_id: str | None = None) -> str:
        """Rotated section list in mos_frame's rail slot. Not mos_strip months."""
        highlight = self._rail_highlight(page_id)
        side = _v(self.mos_layout, "side_menu_position")
        return (
            f"section_rail({self.section_rail_items()}, "
            f"highlight: {highlight}, side: {side})"
        )

    def nav_header_cell(
        self,
        page_id: str | None,
        title: str | None,
        nav_links: list[tuple[str, str] | NavLink] | None = None,
        highlight_months: list[Any] | None = None,
        highlight_quarters: list[Any] | None = None,
        month_link_id: Callable[[Month], str] | None = None,
    ) -> str:
        """Contents rail-adjacent + crumb in the well + chips on the far side."""
        home = self._home_chip()
        crumb = (
            f"trail_heading({title}, [], shrink: true)" if title else "[]"
        )
        far = self._nav_header_far(
            page_id=page_id,
            nav_links=nav_links,
            highlight_months=highlight_months or [],
            highlight_quarters=highlight_quarters or [],
            month_link_id=month_link_id,
        )
        side = _v(self.mos_layout, "side_menu_position")
        return f"nav_header({home}, {crumb}, {far}, side: {side})"

    def _home_chip(self) -> str:
        """Boxed Contents chip is the index link. No five-bar on Scribe nav_header."""
        chip = "box(inset: (x: 1.5mm, y: 0.8mm), stroke: regular_stroke, [Contents])"
        if self.manifest.source(INDEX_ID):
            return f"padded_link(<{INDEX_ID}>, {chip})"
        return chip

    def _nav_header_far(
        self,
        page_id: str | None,
        nav_links: list[tuple[str, str] | NavLink] | None,
        highlight_months: list[Any],
        highlight_quarters: list[Any],
        month_link_id: Callable[[Month], str] | None,
    ) -> str:
        chips: list[str] = []
        highlight_q = set(self._highlight_dests(highlight_quarters))
        highlight_m = set(self._highlight_dests(highlight_months, month_link_id))
        for quarter in walk(self.start_date.quarter(), self.end_date.quarter()):
            dest = self.manifest.dest(quarter.id)
            label = f"{self.i18n.t('quarter.short')}{quarter.number}"
            chips.append(_header_chip(dest, label, dest in highlight_q))
        for month in highlight_months:
            source_id = month_link_id(month) if month_link_id is not None else month.id
            dest = self.manifest.dest(source_id)
            label = self.i18n.t(f"months.short.{month.name}")
            chips.append(_header_chip(dest, label, dest in highlight_m))
        for link in self._nav_links(page_id, nav_links):
            chips.append(link)
        if not chips:
            return "[]"
        return f"stack(dir: ltr, spacing: 2mm, {', '.join(chips)})"

    def _rail_highlight(self, page_id: str | None) -> str:
        name = section_name_for_page_id(page_id)
        if name is None:
            return "none"
        dest = self.manifest.dest(section_dest_id(name, self.configurator))
        return dest

    def heading_menu_grid(
        self,
        page_id: str | None,
        nav_links: list[tuple[str, str] | NavLink] | None = None,
    ) -> str | None:
        links = self._nav_links(page_id, nav_links)
        if not links:
            return None
        height = _v(self.heading, "height")
        return f"""grid(
  rows: {height},
  columns: {len(links)},
  inset: 7pt,

  stroke: (x, y)  => if x > 0 {{ ( left: regular_stroke ) }},
  {", ".join(links)}
)"""

    def _coerce_nav_links(
        self, nav_links: list[tuple[str, str] | NavLink] | None
    ) -> list[NavLink]:
        out: list[NavLink] = []
        if not nav_links:
            return out
        for item in nav_links:
            if isinstance(item, NavLink):
                out.append(item)
            else:
                out.append(NavLink(id=item[0], label=item[1]))
        return out

    def _nav_links(
        self,
        page_id: str | None,
        nav_links: list[tuple[str, str] | NavLink] | None = None,
    ) -> list[str]:
        out: list[str] = []
        for nav in self._coerce_nav_links(nav_links):
            if not self.manifest.source(nav.id):
                continue
            link = f"padded_link(<{nav.id}>, [{nav.label}])"
            if page_id == nav.id:
                out.append(f"grid.cell(fill: black, text(white)[#{link}])")
            else:
                out.append(link)
        return out

    def _highlight_dests(
        self,
        items: list[Any],
        month_link_id: Callable[[Month], str] | None = None,
    ) -> list[str]:
        dests: list[str] = []
        for item in items:
            source_id = month_link_id(item) if month_link_id is not None else item.id
            dest = self.manifest.dest(source_id)
            if dest != "none":
                dests.append(dest)
        return dests


def _tempo_chip(dest: str, label: str, on: bool) -> str:
    flag = "true" if on else "false"
    return f"({dest}, [{label}], {flag})"


def _header_chip(dest: str, label: str, on: bool) -> str:
    ink = f"text(white)[{label}]" if on else f"[{label}]"
    fill = "black" if on else "none"
    box = f"box(inset: (x: 1.5mm, y: 0.8mm), fill: {fill}, stroke: regular_stroke, {ink})"
    if dest != "none":
        return f"padded_link({dest}, {box})"
    return box


def _dest_array(dests: list[str]) -> str:
    if not dests:
        return "()"
    return f"({', '.join(dests)},)"


def _v(mapping, key: str):
    if hasattr(mapping, "__getitem__"):
        return mapping[key]
    return mapping[key]
