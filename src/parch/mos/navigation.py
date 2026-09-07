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
from parch.mos.contents_mark import INDEX_ID, contents_mark
from parch.mos.manifest import Manifest
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
        """Home chip + breadcrumb on the left; month/quarter/context chips on the right."""
        left = self._nav_header_left(title)
        right = self._nav_header_right(
            page_id=page_id,
            nav_links=nav_links,
            highlight_months=highlight_months or [],
            highlight_quarters=highlight_quarters or [],
            month_link_id=month_link_id,
        )
        return f"nav_header({left}, {right})"

    def _nav_header_left(self, title: str | None) -> str:
        home = self._home_chip()
        if title:
            return f"lead_pair({home}, {title}, spacing: 0.5em)"
        return home

    def _home_chip(self) -> str:
        """Contents chip beside the five-bar mark when index is on."""
        mark = contents_mark(self.manifest, None, face="h1")
        chip = "[Contents]"
        if self.manifest.source(INDEX_ID):
            chip = (
                f"padded_link(<{INDEX_ID}>, "
                f"box(inset: (x: 1.5mm, y: 0.8mm), stroke: regular_stroke, [Contents]))"
            )
        if mark:
            return f"lead_pair({mark}, {chip}, spacing: 0.5em)"
        return chip

    def _nav_header_right(
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
