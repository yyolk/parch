"""Canvas helpers: hairlines, type, chrome, mini-months, taps.

fpdf2 user space is top-left, millimetres. `text()` y is a baseline;
`link()` y is the top of the tap rectangle. Keep those separate.

Type: Liberation Serif for titles / cover year; Liberation Sans for chrome,
nav, calendars. Small caps are a fake (uppercase at SMCP_SCALE with tracking).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fpdf import FPDF

from planner.cal import (
    DOW_LETTERS,
    MONTHS_ABBR,
    dest_day,
    dest_month,
    dest_quarter,
    dest_week,
    dest_year,
    mini_month_weeks,
    weeks_spanning,
)

PAGE_W = 106.0
PAGE_H = 144.0

HEADER_H = 9.0
NAV_H = 8.0
GUTTER = 5.5
CONTENT_TOP = HEADER_H + 3.0
CONTENT_BOTTOM = PAGE_H - NAV_H - 2.2

HAIR = 0.18
RULE = 0.12

INK = (0, 0, 0)
PAPER = (255, 255, 255)
MUTED = (112, 112, 112)
GHOST = (168, 168, 168)
WASH = (236, 236, 236)
RULE_C = (198, 198, 198)
SOFT = (210, 210, 210)

FONT_DIR = Path(__file__).resolve().parent / "fonts"
SANS = "Sans"
SERIF = "Serif"
SMCP_SCALE = 0.76
SMCP_TRACK_EM = 0.14


class Book(FPDF):
    """Portrait 106 × 144 mm card. Dest map is filled before emit."""

    def __init__(self, dests: dict[str, int]):
        super().__init__(orientation="P", unit="mm", format=(PAGE_W, PAGE_H))
        self.set_auto_page_break(auto=False)
        self.set_margins(0, 0, 0)
        self.set_compression(True)
        self.dests = dests
        self._page_links: dict[int, int] = {}
        self.add_font(SANS, "", str(FONT_DIR / "LiberationSans-Regular.ttf"))
        self.add_font(SANS, "B", str(FONT_DIR / "LiberationSans-Bold.ttf"))
        self.add_font(SERIF, "", str(FONT_DIR / "LiberationSerif-Regular.ttf"))
        self.add_font(SERIF, "B", str(FONT_DIR / "LiberationSerif-Bold.ttf"))

    def link_to_page(self, page: int) -> int:
        handle = self._page_links.get(page)
        if handle is None:
            handle = self.add_link(page=page)
            self._page_links[page] = handle
        return handle

    def tap(self, x: float, y: float, w: float, h: float, dest: str | None) -> None:
        if not dest:
            return
        page = self.dests.get(dest)
        if page is None:
            return
        self.link(x, y, w, h, self.link_to_page(page))

    def bind_dest(self, name: str) -> None:
        """Bind a named destination to the current page."""
        if name not in self.dests:
            return
        self.set_link(name=name)


def pt_mm(pt: float) -> float:
    return pt * 25.4 / 72.0


def smcp_track(size: float) -> float:
    return pt_mm(size * SMCP_SCALE) * SMCP_TRACK_EM


def smcp_width(pdf: Book, text: str, size: float, family: str, style: str) -> float:
    chars = text.upper()
    if not chars:
        return 0.0
    pdf.set_font(family, style, size * SMCP_SCALE)
    track = smcp_track(size)
    return sum(pdf.get_string_width(ch) for ch in chars) + track * (len(chars) - 1)


def draw_smcp(
    pdf: Book,
    x: float,
    baseline: float,
    text: str,
    size: float,
    family: str,
    style: str,
) -> None:
    chars = text.upper()
    pdf.set_font(family, style, size * SMCP_SCALE)
    track = smcp_track(size)
    cx = x
    last = len(chars) - 1
    for i, ch in enumerate(chars):
        pdf.text(cx, baseline, ch)
        cx += pdf.get_string_width(ch) + (track if i < last else 0)


def text_box(
    pdf: Book,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    size: float = 8,
    style: str = "",
    family: str = SANS,
    color: tuple[int, int, int] = INK,
    align: str = "C",
    small_caps: bool = False,
) -> None:
    """Optically centre `text` in a box. Baseline, not cell-top."""
    if not text:
        return
    pdf.set_text_color(*color)
    if small_caps:
        tw = smcp_width(pdf, text, size, family, style)
        cap = pt_mm(size * SMCP_SCALE) * 0.72
    else:
        pdf.set_font(family, style, size)
        tw = pdf.get_string_width(text)
        cap = pt_mm(size) * 0.72
    baseline = y + (h + cap) / 2.0 - 0.12
    if align == "C":
        tx = x + (w - tw) / 2.0
    elif align == "R":
        tx = x + w - tw
    else:
        tx = x
    if small_caps:
        draw_smcp(pdf, tx, baseline, text, size, family, style)
    else:
        pdf.set_font(family, style, size)
        pdf.text(tx, baseline, text)


def hairline(
    pdf: Book,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: tuple[int, int, int] = RULE_C,
    width: float = HAIR,
) -> None:
    pdf.set_draw_color(*color)
    pdf.set_line_width(width)
    pdf.line(x1, y1, x2, y2)


def fill_rect(
    pdf: Book,
    x: float,
    y: float,
    w: float,
    h: float,
    color: tuple[int, int, int],
) -> None:
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, h, style="F")


def stroke_rect(
    pdf: Book,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    color: tuple[int, int, int] = RULE_C,
    width: float = HAIR,
) -> None:
    pdf.set_draw_color(*color)
    pdf.set_line_width(width)
    pdf.rect(x, y, w, h, style="D")


def header(pdf: Book, title: str, meta: str) -> None:
    fill_rect(pdf, 0, 0, PAGE_W, HEADER_H, INK)
    meta_w = 38.0
    text_box(
        pdf,
        GUTTER,
        0,
        PAGE_W - 2 * GUTTER - meta_w - 1.5,
        HEADER_H,
        title,
        size=11,
        style="B",
        family=SERIF,
        color=PAPER,
        align="L",
    )
    text_box(
        pdf,
        PAGE_W - GUTTER - meta_w,
        0,
        meta_w,
        HEADER_H,
        meta,
        size=7.4,
        family=SANS,
        color=(210, 210, 210),
        align="R",
        small_caps=True,
    )


def nav(pdf: Book, year: int, active: str) -> None:
    y = PAGE_H - NAV_H
    slot = PAGE_W / 5.0
    mondays = weeks_spanning(year)
    first_week = dest_week(mondays[0]) if mondays else None
    first_day = dest_day(date(year, 1, 1))
    items = (
        ("Year", dest_year(), "Year"),
        ("Qtr", dest_quarter(1), "Qtr"),
        ("Mon", dest_month(1), "Mon"),
        ("Wk", first_week, "Wk"),
        ("Day", first_day, "Day"),
    )
    fill_rect(pdf, 0, y, PAGE_W, NAV_H, WASH)
    for i, (label, dest, key) in enumerate(items):
        x = i * slot
        on = key == active
        if on:
            fill_rect(pdf, x, y, slot, NAV_H, INK)
        text_box(
            pdf,
            x,
            y,
            slot,
            NAV_H,
            label,
            size=7.6,
            style="B" if on else "",
            family=SANS,
            color=PAPER if on else INK,
            small_caps=True,
        )
        pdf.tap(x, y, slot, NAV_H, dest)
        if i and not on and items[i - 1][2] != active:
            hairline(pdf, x, y + 1.8, x, y + NAV_H - 1.8, color=SOFT)


def chrome(pdf: Book, year: int, title: str, meta: str, active: str, dest: str) -> None:
    pdf.add_page()
    pdf.bind_dest(dest)
    header(pdf, title, meta)
    nav(pdf, year, active)


def chip(
    pdf: Book,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    dest: str | None,
) -> None:
    stroke_rect(pdf, x, y, w, h, color=INK, width=HAIR)
    text_box(pdf, x, y, w, h, label, size=6.6, family=SANS, color=INK, small_caps=True)
    pdf.tap(x, y, w, h, dest)


def lined_rules(
    pdf: Book,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    pitch: float = 4.15,
) -> None:
    n = max(0, int(h / pitch))
    pdf.set_draw_color(*RULE_C)
    pdf.set_line_width(RULE)
    for i in range(1, n + 1):
        ly = y + i * pitch
        if ly > y + h - 0.15:
            break
        pdf.line(x, ly, x + w, ly)


def mini_month(
    pdf: Book,
    x: float,
    y: float,
    w: float,
    h: float,
    year: int,
    month: int,
    *,
    highlight: date | None = None,
    boxed: bool = True,
) -> None:
    if boxed:
        stroke_rect(pdf, x, y, w, h, color=SOFT, width=HAIR)
    pad = 1.2 if boxed else 0.0
    inner_x = x + pad
    inner_w = w - 2 * pad
    title_h = 3.6
    dow_h = 2.8
    text_box(
        pdf,
        inner_x + 0.4,
        y + 0.4,
        inner_w - 0.8,
        title_h,
        MONTHS_ABBR[month - 1],
        size=7.2,
        style="B",
        family=SANS,
        color=INK,
        align="L",
        small_caps=True,
    )
    pdf.tap(inner_x, y + 0.2, inner_w, title_h + 0.4, dest_month(month))
    grid_y = y + title_h + 0.6
    cw = inner_w / 7.0
    for i, letter in enumerate(DOW_LETTERS):
        text_box(
            pdf,
            inner_x + i * cw,
            grid_y,
            cw,
            dow_h,
            letter,
            size=5.4,
            family=SANS,
            color=MUTED,
            small_caps=True,
        )
    weeks = mini_month_weeks(year, month)
    body_y = grid_y + dow_h
    body_h = (y + h - pad) - body_y - 0.4
    rh = body_h / 6.0
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            cx = inner_x + di * cw
            cy = body_y + wi * rh
            in_month = day.month == month
            in_year = day.year == year
            on = highlight is not None and day == highlight
            if on:
                fill_rect(pdf, cx + 0.15, cy + 0.1, cw - 0.3, rh - 0.15, INK)
                color = PAPER
                style = "B"
            else:
                color = INK if in_month else GHOST
                style = ""
            text_box(
                pdf,
                cx,
                cy,
                cw,
                rh,
                str(day.day),
                size=5.6,
                style=style,
                color=color,
            )
            if in_year:
                pdf.tap(cx, cy, cw, rh, dest_day(day))
