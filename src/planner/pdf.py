"""fpdf2 drawing: compact portrait page, header, section nav, calendars, links."""

from __future__ import annotations

from datetime import date

from fpdf import FPDF

from planner.calendar_model import (
    MONTH_ABBR,
    MONTH_NAMES,
    WEEKDAY_LETTERS,
    YearPlan,
    dest_day,
    dest_days,
    dest_month,
    dest_months,
    dest_quarter,
    dest_quarters,
    dest_weeks,
    dest_year,
)
from planner.dests import PageMap

# SuperNote Nomad-ish canvas (A6 X2 is ~140.4 × 187.2 mm printable; we use a
# smaller "page" that is easy to hold on an e-ink reader preview).
PAGE_W_MM = 106.0
PAGE_H_MM = 144.0
MARGIN_MM = 5.0
HEADER_H_MM = 7.0
NAV_H_MM = 8.0

INK = (25, 25, 25)
MUTE = (105, 105, 105)
RULE = (170, 170, 170)
WASH = (228, 228, 228)
HAIR = (140, 140, 140)

NAV_ITEMS = (
    ("Year", dest_year()),
    ("Qtr", dest_quarters()),
    ("Mon", dest_months()),
    ("Wk", dest_weeks()),
    ("Day", dest_days()),
)

SECTION_YEAR = "year"
SECTION_QUARTER = "quarter"
SECTION_MONTH = "month"
SECTION_WEEK = "week"
SECTION_DAY = "day"


class PlannerPDF(FPDF):
    def __init__(self, plan: YearPlan, pages: PageMap):
        super().__init__(orientation="P", unit="mm", format=(PAGE_W_MM, PAGE_H_MM))
        self.plan = plan
        self.pages_map = pages
        self.set_auto_page_break(auto=False)
        self.set_margins(MARGIN_MM, MARGIN_MM, MARGIN_MM)
        self.set_creator("fpdf2 greenfield planner spike")
        self.set_author("planner spike")
        self.set_title(f"{plan.year} Yearly Planner")
        self.set_compression(True)
        self._section: str | None = None

    # --- destinations / links -------------------------------------------------

    def bind(self, *names: str) -> None:
        """Register named destinations at the current page top."""
        for name in names:
            if name:
                self.add_link(name=name)

    def href(self, name: str | None) -> int | None:
        if not name or not self.pages_map.has(name):
            return None
        return self.add_link(page=self.pages_map.page(name))

    def tap(self, x: float, y: float, w: float, h: float, name: str | None) -> None:
        link = self.href(name)
        if link is not None:
            self.link(x=x, y=y, w=w, h=h, link=link)

    # --- chrome ---------------------------------------------------------------

    def content_top(self) -> float:
        return MARGIN_MM + HEADER_H_MM + 1.0

    def content_bottom(self, *, nav: bool) -> float:
        if nav:
            return PAGE_H_MM - MARGIN_MM - NAV_H_MM - 1.0
        return PAGE_H_MM - MARGIN_MM

    def content_width(self) -> float:
        return PAGE_W_MM - 2 * MARGIN_MM

    def begin_page(self, *, dests: tuple[str, ...], title: str, section: str | None) -> None:
        self.add_page()
        self.bind(*dests)
        self._section = section
        if section is None:
            return
        self._draw_header(title)
        self._draw_nav()

    def _draw_header(self, title: str) -> None:
        x = MARGIN_MM
        y = MARGIN_MM
        w = self.content_width()
        h = HEADER_H_MM
        self.set_font("helvetica", "B", 10)
        self.set_text_color(*INK)
        self.set_xy(x, y)
        self.cell(w * 0.72, h, title, align="L")
        year_s = str(self.plan.year)
        self.set_font("helvetica", "", 9)
        self.set_text_color(*MUTE)
        self.set_xy(x + w * 0.72, y)
        self.cell(w * 0.28, h, year_s, align="R")
        self.tap(x + w * 0.72, y, w * 0.28, h, dest_year())
        self.set_draw_color(*HAIR)
        self.set_line_width(0.2)
        self.line(x, y + h, x + w, y + h)

    def _draw_nav(self) -> None:
        x = MARGIN_MM
        y = PAGE_H_MM - MARGIN_MM - NAV_H_MM
        w = self.content_width()
        h = NAV_H_MM
        n = len(NAV_ITEMS)
        cell_w = w / n
        self.set_draw_color(*HAIR)
        self.set_line_width(0.2)
        self.line(x, y, x + w, y)
        active = {
            SECTION_YEAR: 0,
            SECTION_QUARTER: 1,
            SECTION_MONTH: 2,
            SECTION_WEEK: 3,
            SECTION_DAY: 4,
        }.get(self._section or "", -1)
        for i, (label, dest) in enumerate(NAV_ITEMS):
            cx = x + i * cell_w
            if i == active:
                self.set_fill_color(*WASH)
                self.rect(cx, y, cell_w, h, style="F")
                self.set_font("helvetica", "B", 8)
                self.set_text_color(*INK)
            else:
                self.set_font("helvetica", "", 8)
                self.set_text_color(*MUTE)
            self.set_xy(cx, y)
            self.cell(cell_w, h, label, align="C")
            self.tap(cx, y, cell_w, h, dest)
            if i:
                self.set_draw_color(*RULE)
                self.set_line_width(0.12)
                self.line(cx, y + 1.5, cx, y + h - 1.5)

    # --- primitives -----------------------------------------------------------

    def boxed_label(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        *,
        dest: str | None = None,
        bold: bool = False,
        size: float = 8,
        color: tuple[int, int, int] = INK,
        align: str = "C",
    ) -> None:
        self.set_font("helvetica", "B" if bold else "", size)
        self.set_text_color(*color)
        self.set_xy(x, y)
        self.cell(w, h, text, align=align)
        self.tap(x, y, w, h, dest)

    def lined_panel(self, x: float, y: float, w: float, h: float, *, gap: float = 6.0) -> None:
        self.set_draw_color(*HAIR)
        self.set_line_width(0.25)
        self.rect(x, y, w, h)
        self.set_draw_color(*RULE)
        self.set_line_width(0.1)
        yy = y + gap
        while yy < y + h - 0.8:
            self.line(x + 1.0, yy, x + w - 1.0, yy)
            yy += gap

    def draw_mini_month(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        month: int,
        *,
        title: str | None = None,
        title_dest: str | None = None,
        show_outside: bool = True,
    ) -> None:
        grid = self.plan.month_grid(month)
        title = title if title is not None else MONTH_ABBR[month - 1]
        title_h = 4.2
        dow_h = 3.2
        rows = len(grid)
        body_h = h - title_h - dow_h
        cell_h = body_h / rows
        cell_w = w / 7.0

        self.boxed_label(
            x,
            y,
            w,
            title_h,
            title,
            dest=title_dest or dest_month(month),
            bold=True,
            size=7.5,
            align="L",
        )

        self.set_font("helvetica", "", 5.5)
        self.set_text_color(*MUTE)
        for i, letter in enumerate(WEEKDAY_LETTERS):
            self.set_xy(x + i * cell_w, y + title_h)
            self.cell(cell_w, dow_h, letter, align="C")

        for r, week_days in enumerate(grid):
            row_y = y + title_h + dow_h + r * cell_h
            for c, day in enumerate(week_days):
                cx = x + c * cell_w
                in_month = day.month == month
                in_year = day.year == self.plan.year
                if not in_month and not show_outside:
                    continue
                color = INK if in_month and in_year else MUTE
                self.set_font("helvetica", "", 6)
                self.set_text_color(*color)
                self.set_xy(cx, row_y)
                self.cell(cell_w, cell_h, str(day.day), align="C")
                if in_year:
                    self.tap(cx, row_y, cell_w, cell_h, dest_day(day))

    def draw_month_grid(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        month: int,
        *,
        week_gutter: float = 6.5,
    ) -> None:
        grid = self.plan.month_grid(month)
        dow_h = 4.5
        rows = len(grid)
        body_h = h - dow_h
        cell_h = body_h / rows
        day_w = (w - week_gutter) / 7.0

        self.set_font("helvetica", "", 6)
        self.set_text_color(*MUTE)
        self.set_xy(x, y)
        self.cell(week_gutter, dow_h, "W", align="C")
        for i, letter in enumerate(WEEKDAY_LETTERS):
            self.set_xy(x + week_gutter + i * day_w, y)
            self.cell(day_w, dow_h, letter, align="C")

        self.set_draw_color(*RULE)
        self.set_line_width(0.12)
        for r, week_days in enumerate(grid):
            week = self.plan.week_containing(week_days[0])
            row_y = y + dow_h + r * cell_h
            self.set_font("helvetica", "", 6)
            self.set_text_color(*MUTE)
            self.set_xy(x, row_y)
            # Week index within the year list (1-based among plan.weeks).
            try:
                idx = self.plan.weeks.index(week) + 1
            except ValueError:
                idx = 0
            self.cell(week_gutter, cell_h, str(idx) if idx else "", align="C")
            self.tap(x, row_y, week_gutter, cell_h, week.dest())
            for c, day in enumerate(week_days):
                cx = x + week_gutter + c * day_w
                self.rect(cx, row_y, day_w, cell_h)
                in_month = day.month == month
                in_year = day.year == self.plan.year
                color = INK if in_month else MUTE
                self.set_font("helvetica", "B" if in_month else "", 7)
                self.set_text_color(*color)
                self.set_xy(cx + 0.4, row_y + 0.3)
                self.cell(day_w - 0.8, 3.6, str(day.day), align="L")
                if in_year:
                    self.tap(cx, row_y, day_w, cell_h, dest_day(day))
        # outer frame
        self.set_draw_color(*HAIR)
        self.set_line_width(0.2)
        self.rect(x + week_gutter, y + dow_h, w - week_gutter, body_h)
