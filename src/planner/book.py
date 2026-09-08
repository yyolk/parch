"""Assemble cover / year / quarter / month / week / day pages."""

from __future__ import annotations

from datetime import date, timedelta

from planner.calendar_model import (
    MONTH_NAMES,
    YearPlan,
    dest_cover,
    dest_day,
    dest_days,
    dest_month,
    dest_months,
    dest_quarter,
    dest_quarters,
    dest_weeks,
    dest_year,
)
from planner.dests import PageMap, build_page_map
from planner.pdf import MUTE, PAGE_W_MM, PlannerPDF


def generate(year: int = 2026, *, specimen: bool = False) -> PlannerPDF:
    plan = YearPlan(year=year)
    pages = build_page_map(plan, specimen=specimen)
    pdf = PlannerPDF(plan, pages)
    _emit_cover(pdf)
    _emit_year(pdf)
    quarters = (1,) if specimen else (1, 2, 3, 4)
    for q in quarters:
        _emit_quarter(pdf, q)
    months = (1,) if specimen else tuple(range(1, 13))
    for month in months:
        _emit_month(pdf, month)
    weeks = plan.weeks[:1] if specimen else plan.weeks
    for week in weeks:
        _emit_week(pdf, week.monday)
    days: tuple[date, ...] = (plan.jan1,) if specimen else plan.days
    for day in days:
        _emit_day(pdf, day)
    return pdf


def write_pdf(path: str, year: int = 2026, *, specimen: bool = False) -> str:
    pdf = generate(year, specimen=specimen)
    pdf.output(path)
    return path


def _emit_cover(pdf: PlannerPDF) -> None:
    pdf.begin_page(dests=(dest_cover(),), title="", section=None)
    year = pdf.plan.year
    # Vertical stack, no nav, no section chrome.
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(*MUTE)
    pdf.set_xy(0, 42)
    pdf.cell(PAGE_W_MM, 8, "Yearly Planner", align="C")
    pdf.set_font("helvetica", "B", 42)
    pdf.set_text_color(25, 25, 25)
    pdf.set_xy(0, 54)
    pdf.cell(PAGE_W_MM, 18, str(year), align="C")
    pdf.set_draw_color(140, 140, 140)
    pdf.set_line_width(0.35)
    pdf.line(28, 76, PAGE_W_MM - 28, 76)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(*MUTE)
    pdf.set_xy(12, 82)
    pdf.multi_cell(
        PAGE_W_MM - 24,
        4.4,
        "Monday week start  ·  106 × 144 mm  ·  fpdf2 spike",
        align="C",
    )
    # Tappable year numeral → year page (cover still has no nav bar).
    pdf.tap(28, 54, PAGE_W_MM - 56, 18, dest_year())


def _emit_year(pdf: PlannerPDF) -> None:
    pdf.begin_page(dests=(dest_year(),), title=str(pdf.plan.year), section="year")
    x0 = 5.0
    y0 = pdf.content_top() + 1.0
    gap_x = 2.2
    gap_y = 2.4
    cols, rows = 3, 4
    w = (pdf.content_width() - gap_x * (cols - 1)) / cols
    h = (pdf.content_bottom(nav=True) - y0 - gap_y * (rows - 1)) / rows
    for i in range(12):
        month = i + 1
        c, r = i % cols, i // cols
        pdf.draw_mini_month(
            x0 + c * (w + gap_x),
            y0 + r * (h + gap_y),
            w,
            h,
            month,
            title=MONTH_NAMES[month - 1],
            title_dest=dest_month(month),
        )


def _emit_quarter(pdf: PlannerPDF, quarter: int) -> None:
    dests = (dest_quarter(quarter),)
    if quarter == 1:
        dests = (dest_quarters(), dest_quarter(1))
    pdf.begin_page(dests=dests, title=f"Q{quarter}  {pdf.plan.year}", section="quarter")
    months = pdf.plan.quarter_months(quarter)
    x0 = 5.0
    y0 = pdf.content_top() + 0.5
    bottom = pdf.content_bottom(nav=True)
    notes_h = 28.0
    grid_h = bottom - y0 - notes_h - 3.0
    gap = 2.0
    col_w = (pdf.content_width() - 2 * gap) / 3.0
    for i, month in enumerate(months):
        pdf.draw_mini_month(
            x0 + i * (col_w + gap),
            y0,
            col_w,
            grid_h,
            month,
            title=MONTH_NAMES[month - 1],
            title_dest=dest_month(month),
        )
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(*MUTE)
    pdf.set_xy(x0, y0 + grid_h + 1.2)
    pdf.cell(pdf.content_width(), 3.5, "Notes", align="L")
    pdf.lined_panel(x0, y0 + grid_h + 4.8, pdf.content_width(), notes_h - 5.0, gap=5.5)


def _emit_month(pdf: PlannerPDF, month: int) -> None:
    dests = (dest_month(month),)
    if month == 1:
        dests = (dest_months(), dest_month(1))
    title = f"{MONTH_NAMES[month - 1]}  {pdf.plan.year}"
    pdf.begin_page(dests=dests, title=title, section="month")
    x0 = 5.0
    y0 = pdf.content_top() + 0.4
    pdf.draw_month_grid(
        x0,
        y0,
        pdf.content_width(),
        pdf.content_bottom(nav=True) - y0,
        month,
    )


def _emit_week(pdf: PlannerPDF, monday: date) -> None:
    week = pdf.plan.week_containing(monday)
    dests = (week.dest(),)
    if week == pdf.plan.weeks[0]:
        dests = (dest_weeks(), week.dest())
    label = f"Week of {monday.strftime('%-d %b %Y')}"
    pdf.begin_page(dests=dests, title=label, section="week")
    x0 = 5.0
    y0 = pdf.content_top() + 0.6
    bottom = pdf.content_bottom(nav=True)
    rows = 7
    gap = 1.2
    row_h = (bottom - y0 - gap * (rows - 1)) / rows
    gutter = 16.0
    for i, day in enumerate(week.days):
        y = y0 + i * (row_h + gap)
        in_year = day.year == pdf.plan.year
        pdf.set_draw_color(170, 170, 170)
        pdf.set_line_width(0.15)
        pdf.rect(x0, y, pdf.content_width(), row_h)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(25, 25, 25) if in_year else pdf.set_text_color(*MUTE)
        pdf.set_xy(x0 + 0.6, y + 0.4)
        pdf.cell(gutter, 4.0, day.strftime("%a"), align="L")
        pdf.set_font("helvetica", "", 7)
        pdf.set_xy(x0 + 0.6, y + 4.0)
        pdf.cell(gutter, 4.0, day.strftime("%-d %b"), align="L")
        if in_year:
            pdf.tap(x0, y, gutter + 2.0, row_h, dest_day(day))
            pdf.tap(x0 + gutter, y, 10.0, 4.2, dest_month(day.month))
        # writing well
        pdf.set_draw_color(190, 190, 190)
        pdf.set_line_width(0.08)
        line_y = y + 4.2
        while line_y < y + row_h - 1.0:
            pdf.line(x0 + gutter + 1.0, line_y, x0 + pdf.content_width() - 1.2, line_y)
            line_y += 4.2


def _emit_day(pdf: PlannerPDF, day: date) -> None:
    dests = (dest_day(day),)
    if day == pdf.plan.jan1:
        dests = (dest_days(), dest_day(day))
    title = day.strftime("%A  %-d %B %Y")
    pdf.begin_page(dests=dests, title=title, section="day")
    x0 = 5.0
    y0 = pdf.content_top() + 0.4
    bottom = pdf.content_bottom(nav=True)
    cal_w = 36.0
    cal_h = 32.0
    # Tiny month calendar (month title → month page; cells → days).
    pdf.draw_mini_month(
        x0 + pdf.content_width() - cal_w,
        y0,
        cal_w,
        cal_h,
        day.month,
        title=MONTH_NAMES[day.month - 1],
        title_dest=dest_month(day.month),
        show_outside=False,
    )
    # Prev / next day chips.
    prev_d = day - timedelta(days=1)
    next_d = day + timedelta(days=1)
    pdf.boxed_label(
        x0,
        y0,
        14,
        5.5,
        "< prev",
        dest=dest_day(prev_d) if prev_d.year == pdf.plan.year else None,
        size=7,
        color=MUTE,
        align="L",
    )
    pdf.boxed_label(
        x0 + 16,
        y0,
        14,
        5.5,
        "next >",
        dest=dest_day(next_d) if next_d.year == pdf.plan.year else None,
        size=7,
        color=MUTE,
        align="L",
    )
    notes_y = y0 + cal_h + 2.5
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(*MUTE)
    pdf.set_xy(x0, notes_y)
    pdf.cell(40, 3.6, "Notes", align="L")
    pdf.lined_panel(x0, notes_y + 4.0, pdf.content_width(), bottom - (notes_y + 4.0), gap=6.0)
