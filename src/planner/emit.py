"""Emit cover / year / quarter / month / week / day / notes pages."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from planner.cal import (
    DOW,
    DOW_LETTERS,
    MONTHS,
    MONTHS_ABBR,
    dest_cover,
    dest_day,
    dest_month,
    dest_notes,
    dest_quarter,
    dest_week,
    dest_year,
    days_in_year,
    month_weeks,
    quarter_months,
    quarter_of,
    short_range,
    weeks_spanning,
)
from planner.paint import (
    CONTENT_BOTTOM,
    CONTENT_TOP,
    GUTTER,
    GHOST,
    HAIR,
    INK,
    MUTED,
    PAGE_H,
    PAGE_W,
    SOFT,
    WASH,
    Book,
    chip,
    chrome,
    fill_rect,
    hairline,
    lined_rules,
    mini_month,
    stroke_rect,
    text_box,
)

CONTENT_W = PAGE_W - 2 * GUTTER


@dataclass
class PageSpec:
    dest: str
    kind: str
    payload: object


@dataclass
class Plan:
    year: int
    notes_pages: int = 0
    specimen: bool = False
    dests: dict[str, int] = field(default_factory=dict)
    pages: list[PageSpec] = field(default_factory=list)

    def build(self) -> None:
        specs: list[PageSpec] = [PageSpec(dest_cover(), "cover", None), PageSpec(dest_year(), "year", None)]
        if self.specimen:
            specs.append(PageSpec(dest_quarter(1), "quarter", 1))
            specs.append(PageSpec(dest_month(1), "month", 1))
            first_monday = weeks_spanning(self.year)[0]
            specs.append(PageSpec(dest_week(first_monday), "week", first_monday))
            first = date(self.year, 1, 1)
            specs.append(PageSpec(dest_day(first), "day", first))
            for n in range(1, self.notes_pages + 1):
                specs.append(PageSpec(dest_notes(first, n), "notes", (first, n)))
        else:
            for q in range(1, 5):
                specs.append(PageSpec(dest_quarter(q), "quarter", q))
            for m in range(1, 13):
                specs.append(PageSpec(dest_month(m), "month", m))
            for monday in weeks_spanning(self.year):
                specs.append(PageSpec(dest_week(monday), "week", monday))
            for day in days_in_year(self.year):
                specs.append(PageSpec(dest_day(day), "day", day))
                for n in range(1, self.notes_pages + 1):
                    specs.append(PageSpec(dest_notes(day, n), "notes", (day, n)))
        self.pages = specs
        self.dests = {spec.dest: i + 1 for i, spec in enumerate(specs)}


def write_pdf(path: Path, *, year: int, notes_pages: int, specimen: bool) -> Path:
    plan = Plan(year=year, notes_pages=notes_pages, specimen=specimen)
    plan.build()
    pdf = Book(plan.dests)
    for spec in plan.pages:
        if spec.kind == "cover":
            draw_cover(pdf, year)
        elif spec.kind == "year":
            draw_year(pdf, year)
        elif spec.kind == "quarter":
            draw_quarter(pdf, year, int(spec.payload))
        elif spec.kind == "month":
            draw_month(pdf, year, int(spec.payload))
        elif spec.kind == "week":
            draw_week(pdf, year, spec.payload)  # type: ignore[arg-type]
        elif spec.kind == "day":
            draw_day(pdf, year, spec.payload, notes_pages)  # type: ignore[arg-type]
        elif spec.kind == "notes":
            day, n = spec.payload  # type: ignore[misc]
            draw_notes(pdf, year, day, n, notes_pages)
        else:
            raise ValueError(spec.kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path


def draw_cover(pdf: Book, year: int) -> None:
    pdf.add_page()
    pdf.bind_dest(dest_cover())
    outer, inner = 3.1, 4.5
    stroke_rect(pdf, outer, outer, PAGE_W - 2 * outer, PAGE_H - 2 * outer, color=INK, width=HAIR)
    stroke_rect(pdf, inner, inner, PAGE_W - 2 * inner, PAGE_H - 2 * inner, color=INK, width=HAIR)

    text_box(pdf, 0, 34, PAGE_W, 8, "YEAR BOOK", size=8.5, color=MUTED)
    year_y, year_h = 54, 18
    text_box(pdf, 0, year_y, PAGE_W, year_h, str(year), size=40, style="B", color=INK)
    numeral_w = 42
    pdf.tap((PAGE_W - numeral_w) / 2, year_y, numeral_w, year_h, dest_year())
    text_box(
        pdf,
        GUTTER,
        80,
        CONTENT_W,
        6,
        "monday weeks · 106 × 144 mm",
        size=8,
        color=MUTED,
    )
    text_box(
        pdf,
        GUTTER,
        PAGE_H - inner - 8,
        CONTENT_W,
        5,
        "fpdf2 spike v2",
        size=7,
        color=MUTED,
    )


def draw_year(pdf: Book, year: int) -> None:
    chrome(pdf, year, str(year), "twelve months", "Year", dest_year())
    gap_x, gap_y = 1.8, 1.8
    cols, rows = 3, 4
    grid_h = CONTENT_BOTTOM - CONTENT_TOP
    mw = (CONTENT_W - (cols - 1) * gap_x) / cols
    mh = (grid_h - (rows - 1) * gap_y) / rows
    for i in range(12):
        month = i + 1
        col, row = i % cols, i // cols
        x = GUTTER + col * (mw + gap_x)
        y = CONTENT_TOP + row * (mh + gap_y)
        mini_month(pdf, x, y, mw, mh, year, month)


def draw_quarter(pdf: Book, year: int, quarter: int) -> None:
    months = quarter_months(quarter)
    meta = f"{MONTHS_ABBR[months[0] - 1]}-{MONTHS_ABBR[months[2] - 1]}"
    chrome(pdf, year, f"Q{quarter} {year}", meta, "Qtr", dest_quarter(quarter))
    gap = 1.8
    mh = 38.0
    mw = (CONTENT_W - 2 * gap) / 3.0
    for i, month in enumerate(months):
        x = GUTTER + i * (mw + gap)
        mini_month(pdf, x, CONTENT_TOP, mw, mh, year, month)
    notes_y = CONTENT_TOP + mh + 3.4
    text_box(pdf, GUTTER, notes_y, 20, 3.2, "notes", size=6.2, color=MUTED, align="L")
    lined_rules(pdf, GUTTER, notes_y + 3.4, CONTENT_W, CONTENT_BOTTOM - (notes_y + 3.4), pitch=4.1)


def draw_month(pdf: Book, year: int, month: int) -> None:
    q = quarter_of(month)
    chrome(pdf, year, f"{MONTHS[month - 1]} {year}", f"Q{q}", "Mon", dest_month(month))
    weeks = month_weeks(year, month)
    gutter = 8.0
    grid_x = GUTTER + gutter
    grid_w = PAGE_W - GUTTER - grid_x
    cw = grid_w / 7.0
    y = CONTENT_TOP
    dow_h = 4.2
    for i, letter in enumerate(DOW_LETTERS):
        text_box(pdf, grid_x + i * cw, y, cw, dow_h, letter, size=6.6, color=MUTED)
    hairline(pdf, GUTTER, y + dow_h, PAGE_W - GUTTER, y + dow_h, color=INK, width=HAIR)
    y = y + dow_h + 0.6
    row_h = (CONTENT_BOTTOM - y) / max(len(weeks), 5)
    for week in weeks:
        monday = week[0]
        iso = monday.isocalendar().week
        text_box(
            pdf,
            GUTTER,
            y,
            gutter - 0.4,
            row_h,
            f"W{iso:02d}",
            size=5.6,
            color=MUTED,
            align="L",
        )
        pdf.tap(GUTTER, y, gutter, row_h, dest_week(monday))
        for di, day in enumerate(week):
            cx = grid_x + di * cw
            in_month = day.month == month
            in_year = day.year == year
            text_box(
                pdf,
                cx + 0.6,
                y + 0.8,
                cw - 1.0,
                5.2,
                str(day.day),
                size=8.5,
                style="B" if in_month else "",
                color=INK if in_month else MUTED,
                align="L",
            )
            if in_year:
                pdf.tap(cx, y, cw, row_h, dest_day(day))
        hairline(pdf, GUTTER, y + row_h, PAGE_W - GUTTER, y + row_h, color=SOFT)
        y += row_h


def draw_week(pdf: Book, year: int, monday: date) -> None:
    sunday = monday + timedelta(days=6)
    iso = monday.isocalendar()
    chrome(
        pdf,
        year,
        f"Week {iso.week}",
        short_range(monday, sunday),
        "Wk",
        dest_week(monday),
    )
    rail = 18.0
    row_h = (CONTENT_BOTTOM - CONTENT_TOP) / 7.0
    well_x = GUTTER + rail + 1.2
    well_w = PAGE_W - GUTTER - well_x
    for i in range(7):
        day = monday + timedelta(days=i)
        y = CONTENT_TOP + i * row_h
        in_year = day.year == year
        if in_year:
            fill_rect(pdf, GUTTER, y, rail, row_h, WASH)
        text_box(
            pdf,
            GUTTER + 0.5,
            y + 0.6,
            rail - 1.0,
            3.6,
            DOW[i],
            size=7,
            style="B" if in_year else "",
            color=INK if in_year else MUTED,
            align="L",
        )
        text_box(
            pdf,
            GUTTER + 0.5,
            y + 3.8,
            rail - 1.0,
            3.2,
            f"{day.day} {MONTHS_ABBR[day.month - 1]}",
            size=5.8,
            color=INK if in_year else MUTED,
            align="L",
        )
        if in_year:
            pdf.tap(GUTTER, y, rail + 1.2, row_h, dest_day(day))
        lined_rules(pdf, well_x, y + 0.4, well_w, row_h - 0.8, pitch=3.6)
        hairline(pdf, GUTTER, y + row_h, PAGE_W - GUTTER, y + row_h, color=SOFT)
    hairline(pdf, GUTTER + rail, CONTENT_TOP, GUTTER + rail, CONTENT_BOTTOM, color=SOFT)


def _day_chips(year: int, day: date, notes_pages: int) -> list[tuple[str, str | None]]:
    chips: list[tuple[str, str | None]] = []
    prev = day - timedelta(days=1)
    nxt = day + timedelta(days=1)
    if prev.year == year:
        chips.append(("prev", dest_day(prev)))
    else:
        chips.append(("prev", None))
    if nxt.year == year:
        chips.append(("next", dest_day(nxt)))
    else:
        chips.append(("next", None))
    if notes_pages == 1:
        chips.append(("notes", dest_notes(day, 1)))
    elif 1 < notes_pages <= 4:
        for n in range(1, notes_pages + 1):
            chips.append((f"notes {n}", dest_notes(day, n)))
    elif notes_pages > 4:
        chips.append((f"notes 1/{notes_pages}", dest_notes(day, 1)))
    return chips


def _draw_chip_row(
    pdf: Book,
    y: float,
    items: list[tuple[str, str | None]],
) -> float:
    h = 5.4
    gap = 1.2
    x = GUTTER
    for label, dest in items:
        w = max(12.0, 2.4 + len(label) * 1.55)
        if dest is None:
            stroke_rect(pdf, x, y, w, h, color=SOFT, width=HAIR)
            text_box(pdf, x, y, w, h, label, size=6.5, color=GHOST)
        else:
            chip(pdf, x, y, w, h, label, dest)
        x += w + gap
    return y + h + 2.4


def draw_day(pdf: Book, year: int, day: date, notes_pages: int) -> None:
    title = f"{DOW[day.weekday()]} {day.day} {MONTHS[day.month - 1]}"
    chrome(pdf, year, title, str(year), "Day", dest_day(day))
    y = _draw_chip_row(pdf, CONTENT_TOP, _day_chips(year, day, notes_pages))
    left_w = 33.0
    gap = 2.6
    right_x = GUTTER + left_w + gap
    right_w = PAGE_W - GUTTER - right_x
    cal_h = 34.0
    mini_month(pdf, GUTTER, y, left_w, cal_h, year, day.month, highlight=day)
    more_y = y + cal_h + 2.2
    text_box(pdf, GUTTER, more_y, left_w, 3.0, "more", size=6.2, color=MUTED, align="L")
    lined_rules(pdf, GUTTER, more_y + 3.0, left_w, CONTENT_BOTTOM - (more_y + 3.0), pitch=4.0)
    text_box(pdf, right_x, y, right_w, 3.0, "today", size=6.2, color=MUTED, align="L")
    lined_rules(pdf, right_x, y + 3.0, right_w, CONTENT_BOTTOM - (y + 3.0), pitch=4.0)


def draw_notes(pdf: Book, year: int, day: date, n: int, notes_pages: int) -> None:
    title = f"{day.day} {MONTHS_ABBR[day.month - 1]} · notes {n}/{notes_pages}"
    chrome(pdf, year, title, str(year), "Day", dest_notes(day, n))
    items: list[tuple[str, str | None]] = [("day", dest_day(day))]
    if n > 1:
        items.append(("prev", dest_notes(day, n - 1)))
    else:
        items.append(("prev", None))
    if n < notes_pages:
        items.append(("next", dest_notes(day, n + 1)))
    else:
        items.append(("next", None))
    y = _draw_chip_row(pdf, CONTENT_TOP, items)
    text_box(pdf, GUTTER, y, 20, 3.0, "notes", size=6.2, color=MUTED, align="L")
    lined_rules(pdf, GUTTER, y + 3.0, CONTENT_W, CONTENT_BOTTOM - (y + 3.0), pitch=4.15)
