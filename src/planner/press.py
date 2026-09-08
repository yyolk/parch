"""Canvas-only yearly planner emit (ReportLab open source).

Platypus is a flowable/story engine; these pages are a fixed e-ink card
with tap rects. pdfgen.canvas + bookmarkPage + linkAbsolute is the fit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib.colors import Color, black, white
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from planner.cal import (
    MONTH_NAMES,
    MONTH_SHORT,
    WEEKDAY_MED,
    WEEKDAY_SHORT,
    days_in_year,
    dest_cover,
    dest_day,
    dest_month,
    dest_notes,
    dest_quarter,
    dest_week,
    dest_year,
    month_grid,
    weeks_spanning,
)

PAGE_W = 106 * mm
PAGE_H = 144 * mm
HEADER_H = 11 * mm
NAV_H = 9.5 * mm
GUTTER = 3.5 * mm

INK = Color(0.08, 0.08, 0.08)
INK_DIM = Color(0.42, 0.42, 0.42)
INK_FAINT = Color(0.72, 0.72, 0.72)
WASH = Color(0.93, 0.93, 0.93)
RULE = Color(0.78, 0.78, 0.78)
NAV = ("Year", "Qtr", "Mon", "Wk", "Day")


@dataclass
class PageSpec:
    kind: str
    dest: str
    quarter: int | None = None
    month: int | None = None
    week_days: list[date] = field(default_factory=list)
    day: date | None = None
    note_i: int | None = None
    note_n: int = 0


@dataclass
class Book:
    year: int
    notes_pages: int
    specimen: bool
    pages: list[PageSpec]
    dests: dict[str, int]
    first_week: str
    first_day: str

    def has(self, dest: str | None) -> bool:
        return bool(dest) and dest in self.dests


def plan_book(year: int, notes_pages: int, specimen: bool) -> Book:
    days = days_in_year(year)
    weeks = weeks_spanning(year)
    pages: list[PageSpec] = [
        PageSpec("cover", dest_cover()),
        PageSpec("year", dest_year()),
    ]
    for q in range(1, 5):
        pages.append(PageSpec("quarter", dest_quarter(q), quarter=q))
    for m in range(1, 13):
        pages.append(PageSpec("month", dest_month(m), month=m))
    for wd in weeks:
        pages.append(PageSpec("week", dest_week(wd[0]), week_days=wd))
    for day in days:
        pages.append(PageSpec("day", dest_day(day), day=day))
        for n in range(1, notes_pages + 1):
            pages.append(
                PageSpec(
                    "notes",
                    dest_notes(day, n),
                    day=day,
                    note_i=n,
                    note_n=notes_pages,
                )
            )

    first_week = dest_week(weeks[0][0])
    first_day = dest_day(days[0])
    if specimen:
        keep = {
            dest_cover(),
            dest_year(),
            dest_quarter(1),
            dest_month(1),
            first_week,
            first_day,
        }
        for n in range(1, notes_pages + 1):
            keep.add(dest_notes(days[0], n))
        pages = [p for p in pages if p.dest in keep]

    dests = {p.dest: i + 1 for i, p in enumerate(pages)}
    return Book(year, notes_pages, specimen, pages, dests, first_week, first_day)


def write_planner(
    year: int,
    notes_pages: int,
    specimen: bool,
    output: Path,
) -> Path:
    book = plan_book(year, notes_pages, specimen)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output), pagesize=(PAGE_W, PAGE_H))
    canvas.setTitle(f"{year} planner")
    canvas.setAuthor("reportlab spike")
    for spec in book.pages:
        _draw_page(canvas, book, spec)
        canvas.showPage()
    _publish_named_dests(canvas)
    canvas.save()
    return output


def _publish_named_dests(canvas: Canvas) -> None:
    """Put bookmarkPage dests on the catalog so pypdf can count them.

    ReportLab binds Destination objects for linkAbsolute, but does not emit
    Catalog /Dests unless something else asks. The name tree is what the bench
    (and mid-year spot-check) treat as named destinations.
    """
    dests = canvas._destinations
    if not dests:
        return
    from reportlab.pdfbase import pdfdoc

    canvas._doc.Catalog.Dests = pdfdoc.PDFDictionary(dests)


def _draw_page(c: Canvas, book: Book, spec: PageSpec) -> None:
    c.bookmarkPage(spec.dest, fit="Fit")
    if spec.kind == "cover":
        _cover(c, book)
        return
    if spec.kind == "year":
        _year(c, book)
    elif spec.kind == "quarter":
        _quarter(c, book, spec.quarter or 1)
    elif spec.kind == "month":
        _month(c, book, spec.month or 1)
    elif spec.kind == "week":
        _week(c, book, spec.week_days)
    elif spec.kind == "day":
        _day(c, book, spec.day)  # type: ignore[arg-type]
    elif spec.kind == "notes":
        _notes(c, book, spec.day, spec.note_i or 1, spec.note_n)  # type: ignore[arg-type]
    _nav(c, book, spec.kind)


def _hop(c: Canvas, book: Book, dest: str | None, x: float, y: float, w: float, h: float, label: str = "") -> None:
    if not book.has(dest):
        return
    c.linkAbsolute(label or dest or "", dest, Rect=(x, y, x + w, y + h), Border="[0 0 0]")


def _slab(c: Canvas, x: float, y: float, w: float, h: float, fill: Color, stroke: Color | None = None, lw: float = 0.4) -> None:
    c.setFillColor(fill)
    if stroke is None:
        c.rect(x, y, w, h, fill=1, stroke=0)
        return
    c.setStrokeColor(stroke)
    c.setLineWidth(lw)
    c.rect(x, y, w, h, fill=1, stroke=1)


def _label(
    c: Canvas,
    text: str,
    x: float,
    y: float,
    size: float,
    font: str = "Helvetica",
    color: Color = INK,
    align: str = "left",
) -> None:
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "center":
        c.drawCentredString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)


def _baseline(y: float, h: float, size: float) -> float:
    return y + (h - size) * 0.5 + size * 0.12


def _header(c: Canvas, title: str, meta: str = "") -> None:
    _slab(c, 0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, INK)
    _label(c, title, GUTTER, _baseline(PAGE_H - HEADER_H, HEADER_H, 9), 9, "Helvetica-Bold", white)
    if meta:
        _label(
            c,
            meta,
            PAGE_W - GUTTER,
            _baseline(PAGE_H - HEADER_H, HEADER_H, 7),
            7,
            color=Color(0.75, 0.75, 0.75),
            align="right",
        )


def _nav(c: Canvas, book: Book, kind: str) -> None:
    active = {
        "year": 0,
        "quarter": 1,
        "month": 2,
        "week": 3,
        "day": 4,
        "notes": 4,
    }.get(kind, 0)
    landings = (
        dest_year(),
        dest_quarter(1),
        dest_month(1),
        book.first_week,
        book.first_day,
    )
    _slab(c, 0, 0, PAGE_W, NAV_H, WASH)
    c.setStrokeColor(INK)
    c.setLineWidth(0.6)
    c.line(0, NAV_H, PAGE_W, NAV_H)
    tab_w = PAGE_W / 5
    for i, name in enumerate(NAV):
        x = i * tab_w
        if i == active:
            _slab(c, x, 0, tab_w, NAV_H, INK)
            _label(c, name, x + tab_w / 2, _baseline(0, NAV_H, 8), 8, "Helvetica-Bold", white, "center")
        else:
            _label(c, name, x + tab_w / 2, _baseline(0, NAV_H, 8), 8, color=INK, align="center")
            if i:
                c.setStrokeColor(INK_FAINT)
                c.setLineWidth(0.4)
                c.line(x, 1.4 * mm, x, NAV_H - 1.4 * mm)
        _hop(c, book, landings[i], x, 0, tab_w, NAV_H, name)


def _well() -> tuple[float, float, float, float]:
    x = GUTTER
    y = NAV_H + GUTTER
    w = PAGE_W - 2 * GUTTER
    h = PAGE_H - HEADER_H - NAV_H - 2 * GUTTER
    return x, y, w, h


def _rules(c: Canvas, x: float, y: float, w: float, h: float, gap: float = 5.2 * mm) -> None:
    c.setStrokeColor(RULE)
    c.setLineWidth(0.35)
    yy = y + gap
    top = y + h - 0.6 * mm
    while yy < top:
        c.line(x, yy, x + w, yy)
        yy += gap


def _chip(c: Canvas, book: Book, dest: str | None, x: float, y: float, w: float, h: float, text: str, on: bool = False) -> None:
    if on:
        _slab(c, x, y, w, h, INK, INK, 0.4)
        _label(c, text, x + w / 2, _baseline(y, h, 7), 7, "Helvetica-Bold", white, "center")
    else:
        _slab(c, x, y, w, h, white, INK, 0.45)
        _label(c, text, x + w / 2, _baseline(y, h, 7), 7, color=INK, align="center")
    _hop(c, book, dest, x, y, w, h, text)


def _mini_month(
    c: Canvas,
    book: Book,
    year: int,
    month: int,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    title_link: bool = True,
    mark: date | None = None,
) -> None:
    title_h = 4.2 * mm
    _label(
        c,
        MONTH_SHORT[month],
        x + 0.4 * mm,
        y + h - title_h + 0.6 * mm,
        7,
        "Helvetica-Bold",
        INK,
    )
    if title_link:
        _hop(c, book, dest_month(month), x, y + h - title_h, w, title_h, MONTH_NAMES[month])
    grid_y = y
    grid_h = h - title_h
    rows = month_grid(year, month)
    cols = 7
    cw = w / cols
    rh = grid_h / (len(rows) + 1)
    for i, wd in enumerate(WEEKDAY_SHORT):
        _label(c, wd, x + (i + 0.5) * cw, grid_y + grid_h - rh + 0.7 * mm, 5.5, color=INK_DIM, align="center")
    for r, week in enumerate(rows):
        for col, day in enumerate(week):
            cx = x + col * cw
            cy = grid_y + grid_h - (r + 2) * rh
            in_month = day.month == month
            in_year = day.year == book.year
            if mark and day == mark:
                _slab(c, cx + 0.2 * mm, cy + 0.15 * mm, cw - 0.4 * mm, rh - 0.3 * mm, INK)
                _label(c, str(day.day), cx + cw / 2, _baseline(cy, rh, 6), 6, "Helvetica-Bold", white, "center")
            else:
                color = INK if in_month else INK_FAINT
                _label(c, str(day.day), cx + cw / 2, _baseline(cy, rh, 6), 6, color=color, align="center")
            if in_year:
                _hop(c, book, dest_day(day), cx, cy, cw, rh, day.isoformat())


def _cover(c: Canvas, book: Book) -> None:
    _slab(c, 0, 0, PAGE_W, PAGE_H, white)
    inset = 7 * mm
    c.setStrokeColor(INK)
    c.setLineWidth(1.1)
    c.rect(inset, inset, PAGE_W - 2 * inset, PAGE_H - 2 * inset, fill=0, stroke=1)
    c.setLineWidth(0.35)
    c.rect(inset + 1.6 * mm, inset + 1.6 * mm, PAGE_W - 2 * inset - 3.2 * mm, PAGE_H - 2 * inset - 3.2 * mm, fill=0, stroke=1)
    _label(c, "YEAR BOOK", PAGE_W / 2, PAGE_H * 0.70, 11, "Helvetica", INK_DIM, "center")
    year_s = str(book.year)
    _label(c, year_s, PAGE_W / 2, PAGE_H * 0.46, 36, "Helvetica-Bold", INK, "center")
    # tap the year numeral
    _hop(c, book, dest_year(), PAGE_W / 2 - 22 * mm, PAGE_H * 0.44, 44 * mm, 18 * mm, year_s)
    _label(
        c,
        "monday weeks  ·  106 × 144 mm",
        PAGE_W / 2,
        PAGE_H * 0.28,
        7.5,
        color=INK_DIM,
        align="center",
    )
    _label(c, "reportlab spike", PAGE_W / 2, PAGE_H * 0.18, 7, color=INK_FAINT, align="center")


def _year(c: Canvas, book: Book) -> None:
    _header(c, str(book.year), "twelve months")
    x, y, w, h = _well()
    cols, rows = 3, 4
    gap = 2.2 * mm
    cw = (w - gap * (cols - 1)) / cols
    rh = (h - gap * (rows - 1)) / rows
    for i in range(12):
        m = i + 1
        col = i % cols
        row = i // cols
        mx = x + col * (cw + gap)
        my = y + (rows - 1 - row) * (rh + gap)
        _slab(c, mx, my, cw, rh, white, INK_FAINT, 0.35)
        _mini_month(c, book, book.year, m, mx + 1.0 * mm, my + 0.8 * mm, cw - 2.0 * mm, rh - 1.6 * mm)


def _quarter(c: Canvas, book: Book, q: int) -> None:
    start = (q - 1) * 3 + 1
    months = (start, start + 1, start + 2)
    _header(c, f"Q{q}  {book.year}", f"{MONTH_SHORT[start]}–{MONTH_SHORT[start + 2]}")
    x, y, w, h = _well()
    cal_h = h * 0.48
    gap = 2.0 * mm
    cw = (w - 2 * gap) / 3
    for i, m in enumerate(months):
        mx = x + i * (cw + gap)
        _slab(c, mx, y + h - cal_h, cw, cal_h, white, INK_FAINT, 0.35)
        _mini_month(c, book, book.year, m, mx + 1.0 * mm, y + h - cal_h + 0.8 * mm, cw - 2.0 * mm, cal_h - 1.6 * mm)
    notes_y = y
    notes_h = h - cal_h - 3.0 * mm
    _label(c, "notes", x, notes_y + notes_h - 3.4 * mm, 7, color=INK_DIM)
    _rules(c, x, notes_y, w, notes_h - 4.0 * mm)


def _month(c: Canvas, book: Book, month: int) -> None:
    q = (month - 1) // 3 + 1
    _header(c, f"{MONTH_NAMES[month]} {book.year}", f"Q{q}")
    x, y, w, h = _well()
    grid = month_grid(book.year, month)
    gutter = 8.5 * mm
    head_h = 5.0 * mm
    body_h = h - head_h
    rows = len(grid)
    rh = body_h / rows
    cw = (w - gutter) / 7
    for i, wd in enumerate(WEEKDAY_SHORT):
        _label(
            c,
            wd,
            x + gutter + (i + 0.5) * cw,
            _baseline(y + h - head_h, head_h, 7),
            7,
            "Helvetica-Bold",
            INK_DIM,
            "center",
        )
    c.setStrokeColor(INK)
    c.setLineWidth(0.45)
    c.line(x, y + h - head_h, x + w, y + h - head_h)
    for r, week in enumerate(grid):
        cy = y + body_h - (r + 1) * rh
        monday = week[0]
        iso = monday.isocalendar()
        _label(c, f"W{iso.week:02d}", x + gutter / 2, _baseline(cy, rh, 6), 6, color=INK_DIM, align="center")
        _hop(c, book, dest_week(monday), x, cy, gutter, rh, dest_week(monday))
        for col, day in enumerate(week):
            cx = x + gutter + col * cw
            in_month = day.month == month
            in_year = day.year == book.year
            if r < rows:
                c.setStrokeColor(WASH)
                c.setLineWidth(0.3)
                c.line(x + gutter, cy, x + w, cy)
            color = INK if in_month else INK_FAINT
            font = "Helvetica-Bold" if in_month else "Helvetica"
            _label(c, str(day.day), cx + 1.2 * mm, cy + rh - 4.2 * mm, 8, font, color)
            if in_year:
                _hop(c, book, dest_day(day), cx, cy, cw, rh, day.isoformat())


def _week(c: Canvas, book: Book, week_days: list[date]) -> None:
    monday = week_days[0]
    sunday = week_days[-1]
    span = f"{monday.day} {MONTH_SHORT[monday.month]} – {sunday.day} {MONTH_SHORT[sunday.month]}"
    _header(c, f"Week {monday.isocalendar().week}", span)
    x, y, w, h = _well()
    rh = h / 7
    for i, day in enumerate(week_days):
        cy = y + h - (i + 1) * rh
        in_year = day.year == book.year
        _slab(c, x, cy, 18 * mm, rh, WASH if in_year else white, INK_FAINT, 0.3)
        _label(c, WEEKDAY_MED[i], x + 1.2 * mm, cy + rh - 3.8 * mm, 6.5, "Helvetica-Bold", INK if in_year else INK_FAINT)
        _label(c, f"{day.day} {MONTH_SHORT[day.month]}", x + 1.2 * mm, cy + 1.6 * mm, 7, color=INK if in_year else INK_FAINT)
        if in_year:
            _hop(c, book, dest_day(day), x, cy, 18 * mm, rh, day.isoformat())
        c.setStrokeColor(RULE)
        c.setLineWidth(0.35)
        c.line(x + 19 * mm, cy + rh * 0.38, x + w, cy + rh * 0.38)
        c.line(x + 19 * mm, cy + rh * 0.68, x + w, cy + rh * 0.68)
        c.setStrokeColor(INK_FAINT)
        c.setLineWidth(0.3)
        c.line(x, cy, x + w, cy)


def _day(c: Canvas, book: Book, day: date) -> None:
    title = f"{WEEKDAY_MED[day.weekday()]}  {day.day} {MONTH_NAMES[day.month]}"
    _header(c, title, str(book.year))
    x, y, w, h = _well()
    chip_h = 6.2 * mm
    prev_d = day - timedelta(days=1)
    next_d = day + timedelta(days=1)
    prev_dest = dest_day(prev_d) if prev_d.year == book.year else None
    next_dest = dest_day(next_d) if next_d.year == book.year else None
    cw = 16 * mm
    _chip(c, book, prev_dest, x, y + h - chip_h, cw, chip_h, "prev")
    _chip(c, book, next_dest, x + cw + 1.4 * mm, y + h - chip_h, cw, chip_h, "next")
    if book.notes_pages:
        nx = x + 2 * (cw + 1.4 * mm)
        nw = 11 * mm
        for n in range(1, book.notes_pages + 1):
            _chip(c, book, dest_notes(day, n), nx + (n - 1) * (nw + 1.0 * mm), y + h - chip_h, nw, chip_h, f"n{n}")

    cal_w = w * 0.42
    cal_h = h * 0.42
    cal_y = y + h - chip_h - 2.2 * mm - cal_h
    _slab(c, x, cal_y, cal_w, cal_h, white, INK_FAINT, 0.35)
    _mini_month(
        c,
        book,
        day.year,
        day.month,
        x + 1.0 * mm,
        cal_y + 0.6 * mm,
        cal_w - 2.0 * mm,
        cal_h - 1.2 * mm,
        mark=day,
    )
    notes_x = x + cal_w + 2.2 * mm
    notes_w = w - cal_w - 2.2 * mm
    notes_top = y + h - chip_h - 2.2 * mm
    notes_h = notes_top - y
    _label(c, "today", notes_x, notes_top - 3.2 * mm, 7, color=INK_DIM)
    _rules(c, notes_x, y, notes_w, notes_h - 4.0 * mm)
    # leftover well under the mini month
    under_h = cal_y - y - 1.6 * mm
    if under_h > 12 * mm:
        _label(c, "more", x, cal_y - 4.0 * mm, 7, color=INK_DIM)
        _rules(c, x, y, cal_w, under_h - 4.6 * mm)


def _notes(c: Canvas, book: Book, day: date, note_i: int, note_n: int) -> None:
    _header(c, f"{day.day} {MONTH_SHORT[day.month]}  notes {note_i}/{note_n}", str(book.year))
    x, y, w, h = _well()
    chip_h = 6.2 * mm
    _chip(c, book, dest_day(day), x, y + h - chip_h, 16 * mm, chip_h, "day")
    prev_dest = dest_notes(day, note_i - 1) if note_i > 1 else None
    next_dest = dest_notes(day, note_i + 1) if note_i < note_n else None
    _chip(c, book, prev_dest, x + 17.4 * mm, y + h - chip_h, 16 * mm, chip_h, "prev")
    _chip(c, book, next_dest, x + 34.8 * mm, y + h - chip_h, 16 * mm, chip_h, "next")
    _rules(c, x, y, w, h - chip_h - 2.0 * mm, gap=5.6 * mm)
