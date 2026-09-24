"""Painters take ``plotter: Plotter``. Components never draw themselves."""

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import assert_never

from parch.calendar import MONTH_NAMES, WEEKDAY_LABELS, short_date_range
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    BujoIndex,
    BujoKey,
    BujoKeySymbol,
    Checkoff365,
    CollectionLeaf,
    CoverTitle,
    DotGridPad,
    EngineeringPad,
    FavoritesPage,
    FutureLogPage,
    HabitGrid,
    LinedPad,
    MeetingAgenda,
    MeetingIndex,
    MonthGrid,
    MonthlyCalendarList,
    MonthlyTaskWell,
    My100Page,
    Notes,
    PerspectivePad,
    Priorities,
    ProjectsBoard,
    ProjectsIndex,
    ProjectTicket,
    QuarterGrid,
    RapidLogPage,
    ReviewDay,
    ReviewIndex,
    ReviewWeek,
    ReviewWeekPage,
    Schedule,
    StenoPad,
    TasksIndex,
    TasksWeekPage,
    TaskWeek,
    WeekStrip,
)
from parch.devices.registry import NAV_H, NOMAD, Device
from parch.fonts.metrics import (
    fit_line_size,
    glyph_ink,
    ink_rect,
    origin_for_nest,
    pt_mm,
)
from parch.fonts.ramp import EffectiveRamp, Pt, TypeInk, TypeRamp, TypeRef
from parch.geom import Rect
from parch.layouts.planner.hour_shade import shade_painted_hour
from parch.plotter.protocol import Plotter, TextAlign
from parch.sections.page import Page
from parch.tracks import columns, rows

HAIR = 0.18
RULE = 0.12
INK = 0.0
MUTED = 112 / 255
GHOST = 168 / 255
WASH = 236 / 255
SOFT = 210 / 255
RULE_C = 198 / 255
PAPER = 1.0
# Cover display well: inner frame plus air so ink stays off the stroke.
COVER_FRAME_INNER = 4.6
COVER_TITLE_PAD = 1.0
LINE_PITCH = 4.15  # notes / lined-pad ruling — not a Spec/TOML knob

HEADER_H = 9.0
COL_GAP = 3.0
DAILY_MINI_H = 34.0
DAILY_MINI_GAP = 2.2
DAILY_COL_WEIGHTS = (0.34, 0.66)
DAILY_PRIO_GAP = 2.2


def _bound_ramp(plotter: Plotter, ramp: TypeRamp | None) -> TypeRamp:
    resolved = EffectiveRamp() if ramp is None else ramp
    plotter.ramp = resolved
    return resolved


def _cover_headline_ink(headline: str, well: Rect, ramp: TypeRamp) -> TypeInk:
    """Display ink, shrunk so the headline stays one line inside ``well``."""
    ink = ramp.ink("display")
    path = str(ramp.catalog.path(ink.family, ink.weight))
    size = fit_line_size(path, headline, float(ink.size), well.w)
    if size == float(ink.size):
        return ink
    return TypeInk(family=ink.family, weight=ink.weight, size=Pt(size))


def _ink_text(
    plotter: Plotter,
    box: Rect,
    content: str,
    mark: TypeInk | TypeRef,
    *,
    gray: float = 0.0,
    align: TextAlign = "left",
    small_caps: bool = False,
    origin: tuple[float, float] | None = None,
) -> None:
    if isinstance(mark, TypeRef):
        plotter.text(
            box,
            content,
            ref=mark,
            gray=gray,
            align=align,
            small_caps=small_caps,
            origin=origin,
        )
        return
    plotter.text(
        box,
        content,
        ink=mark,
        gray=gray,
        align=align,
        small_caps=small_caps,
        origin=origin,
    )


def paint_header(
    plotter: Plotter,
    device: Device,
    title: str,
    meta: str,
    meta_dest: str | None = None,
    *,
    ramp: TypeRamp,
    chip: str = "",
    chip_dest: str | None = None,
) -> None:
    """One INK rect from y=0 through top_clearance + HEADER_H. Hits stay at content_top."""
    band = Rect(0.0, 0.0, device.page_width, device.top_clearance + HEADER_H)
    plotter.rect(band, stroke=False, fill=True, fill_gray=INK)
    seat = Rect(0.0, device.content_top, device.page_width, HEADER_H)
    gutter = device.writing_clearance
    meta_w = 18.0
    chip_w = 16.0 if chip else 0.0
    title_box = Rect(
        gutter, seat.y, device.page_width - 2 * gutter - meta_w - chip_w - 1.5, seat.h
    )
    plotter.ramp = ramp
    _ink_text(
        plotter, title_box, title, TypeRef(step="title"), gray=PAPER, align="left"
    )
    chrome = TypeRef(step="chrome")
    if chip:
        chip_box = Rect(
            device.page_width - gutter - meta_w - chip_w - 1.2, seat.y, chip_w, seat.h
        )
        _ink_text(
            plotter,
            chip_box,
            chip,
            chrome,
            gray=SOFT,
            align="right",
            small_caps=True,
        )
        if chip_dest:
            plotter.link(chip_box, chip_dest)
    if meta:
        meta_box = Rect(device.page_width - gutter - meta_w, seat.y, meta_w, seat.h)
        _ink_text(
            plotter,
            meta_box,
            meta,
            chrome,
            gray=SOFT,
            align="right",
            small_caps=True,
        )
        if meta_dest:
            plotter.link(meta_box, meta_dest)


def paint_nav(
    plotter: Plotter,
    device: Device,
    items: tuple[tuple[str, str], ...],
    active: str,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    if not items:
        return
    ramp = _bound_ramp(plotter, ramp)
    y = device.page_height - device.bottom_clearance - NAV_H
    slot = device.page_width / len(items)
    plotter.rect(
        Rect(0.0, y, device.page_width, NAV_H + device.bottom_clearance),
        stroke=False,
        fill=True,
        fill_gray=WASH,
    )
    for i, (label, dest) in enumerate(items):
        x = i * slot
        hit = Rect(x, y, slot, NAV_H)
        on = label == active
        if on:
            plotter.rect(
                Rect(x, y, slot, NAV_H + device.bottom_clearance),
                stroke=False,
                fill=True,
                fill_gray=INK,
            )
        chrome = TypeRef(step="chrome", emphasis="strong" if on else "regular")
        _ink_text(
            plotter,
            hit,
            label,
            chrome,
            gray=PAPER if on else INK,
            small_caps=True,
            align="center",
        )
        plotter.link(hit, dest)
        if i and not on:
            prev_on = items[i - 1][0] == active
            if not prev_on:
                plotter.line(
                    x, y + 1.8, x, y + NAV_H - 1.8, stroke_width=HAIR, stroke_gray=SOFT
                )


def paint_cover(
    plotter: Plotter, device: Device, cover: CoverTitle, *, ramp: TypeRamp
) -> None:
    top = device.content_top
    outer, inner = 3.2, COVER_FRAME_INNER
    # Frame sits below top clearance and above unmarked bottom OS chrome.
    ox, oy = outer, max(outer, top + 0.6)
    o_bottom = max(outer, device.bottom_clearance + 0.6)
    plotter.rect(
        Rect(ox, oy, device.page_width - 2 * ox, device.page_height - oy - o_bottom),
        stroke=True,
        fill=False,
        stroke_width=HAIR,
        stroke_gray=INK,
    )
    ix, iy = inner, max(inner, top + 1.8)
    i_bottom = max(inner, device.bottom_clearance + 1.8)
    plotter.rect(
        Rect(ix, iy, device.page_width - 2 * ix, device.page_height - iy - i_bottom),
        stroke=True,
        fill=False,
        stroke_width=HAIR,
        stroke_gray=INK,
    )

    plotter.ramp = ramp
    if cover.display_title:
        brow_text = str(cover.year) if cover.year else ""
        headline = cover.display_title
    else:
        brow_text = cover.eyebrow
        headline = str(cover.year)
    if brow_text:
        brow = Rect(0.0, 38.0, device.page_width, 8.0)
        _ink_text(
            plotter,
            brow,
            brow_text,
            TypeRef(step="eyebrow"),
            gray=MUTED,
            small_caps=True,
            align="center",
        )
    year_box = Rect(0.0, 56.0, device.page_width, 20.0)
    well = Rect(
        ix + COVER_TITLE_PAD,
        year_box.y,
        device.page_width - 2 * (ix + COVER_TITLE_PAD),
        year_box.h,
    )
    _ink_text(
        plotter,
        well,
        headline,
        _cover_headline_ink(headline, well, ramp),
        gray=INK,
        align="center",
    )
    tap_w = 48.0
    plotter.link(
        Rect((device.page_width - tap_w) / 2, year_box.y, tap_w, year_box.h),
        cover.cta_dest,
    )
    specs = Rect(
        device.writing_clearance,
        84.0,
        device.page_width - 2 * device.writing_clearance,
        6.5,
    )
    dims = f"{device.page_width:g} × {device.page_height:g} mm"
    specs_line = f"{cover.specs_lead}  ·  {dims}" if cover.specs_lead else dims
    _ink_text(
        plotter,
        specs,
        specs_line,
        TypeRef(step="body"),
        gray=MUTED,
        small_caps=True,
        align="center",
    )


def paint_annual(
    plotter: Plotter, box: Rect, grid: AnnualGrid, *, ramp: TypeRamp | None = None
) -> None:
    ramp = _bound_ramp(plotter, ramp)
    for r, band in enumerate(rows(box, 4, gap=2.6)):
        for c, cell in enumerate(columns(band, 3, gap=3.4)):
            _paint_mini_month(plotter, cell, grid.months[r * 3 + c], ramp=ramp)


# Product pick: dense pack + 0.90× micro.
# Nomad scores ~18 cols / ~5.33 mm marks. Score bias only — not a hardcoded return.
CHECKOFF_GAP = 0.30
CHECKOFF_MARK_FRAC = 0.91
CHECKOFF_CIRCLE_SEGS = 32
CHECKOFF_COL_PREF = 16
CHECKOFF_COL_PENALTY = 0.08
CHECKOFF_DIAMOND_STROKE = HAIR * 1.4
CHECKOFF_NUMERAL_GRAY = MUTED
CHECKOFF_NUMERAL_SCALE = 0.90
CHECKOFF_LABEL_INSET = 0.18


def checkoff_milestone(day: int) -> bool:
    """Every 10th day is a diamond marker (10, 20, …)."""
    return day > 0 and day % 10 == 0


def checkoff_columns(well: Rect, days: int) -> int:
    """Column count from well geometry + day count.

    Prefer larger seats; extra columns past the ~16 reference are lightly
    penalized so Nomad's dense pack scores ~18 without hardcoding a column.
    """
    n = max(1, days)
    best_cols = 1
    best_score = float("-inf")
    max_cols = min(n, max(1, int(well.w)))
    for cols in range(1, max_cols + 1):
        row_n = (n + cols - 1) // cols
        inner_w = well.w - CHECKOFF_GAP * (cols - 1)
        inner_h = well.h - CHECKOFF_GAP * (row_n - 1)
        if inner_w <= 0 or inner_h <= 0:
            continue
        size = min(inner_w / cols, inner_h / row_n)
        score = size - CHECKOFF_COL_PENALTY * max(0, cols - CHECKOFF_COL_PREF)
        if score > best_score:
            best_score = score
            best_cols = cols
    return best_cols


def checkoff_seats(well: Rect, days: int) -> tuple[Rect, ...]:
    """Equal row tracks fill the well; leftover last-row cells stay empty."""
    n = max(1, days)
    cols = checkoff_columns(well, n)
    row_n = (n + cols - 1) // cols
    seats: list[Rect] = []
    remaining = n
    for band in rows(well, row_n, gap=CHECKOFF_GAP):
        take = min(cols, remaining)
        seats.extend(columns(band, cols, gap=CHECKOFF_GAP)[:take])
        remaining -= take
        if remaining <= 0:
            break
    return tuple(seats)


def checkoff_mark(cell: Rect) -> Rect:
    """Largest inscribed square, inset so neighboring marks do not touch."""
    s = min(cell.w, cell.h) * CHECKOFF_MARK_FRAC
    return Rect(cell.x + (cell.w - s) / 2, cell.y + (cell.h - s) / 2, s, s)


def checkoff_label(mark: Rect) -> Rect:
    """Concentric inset of the mark — padding from the stroke, not the seat width."""
    pad = min(mark.w, mark.h) * CHECKOFF_LABEL_INSET
    return mark.inset(pad)


def checkoff_numeral_ink(ramp: TypeRamp) -> TypeInk:
    """Micro scaled down, medium weight. Strong flooded the mark; book stayed muddy."""
    base = ramp.ink("micro")
    return TypeInk(
        family=base.family,
        weight="medium",
        size=Pt(float(base.size) * CHECKOFF_NUMERAL_SCALE),
    )


def paint_checkoff_365(
    plotter: Plotter,
    box: Rect,
    sheet: Checkoff365,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """1…N circle grid; diamonds on every 10th day. Chrome owns the title."""
    ramp = _bound_ramp(plotter, ramp)
    numeral = checkoff_numeral_ink(ramp)
    dests = sheet.day_dests
    for day, seat in enumerate(checkoff_seats(box, sheet.days), start=1):
        mark = checkoff_mark(seat)
        label = checkoff_label(mark)
        if checkoff_milestone(day):
            _paint_diamond(plotter, mark, stroke_width=CHECKOFF_DIAMOND_STROKE)
        else:
            _stroke_circle(plotter, mark)
        _ink_text(
            plotter,
            label,
            str(day),
            numeral,
            gray=CHECKOFF_NUMERAL_GRAY,
            align="center",
        )
        if day <= len(dests) and dests[day - 1]:
            plotter.link(mark, dests[day - 1])


MY_100_COUNT = 100
MY_100_MIN_COL_W = 32.0
MY_100_MIN_ROW_H = 5.6
MY_100_COL_GAP = COL_GAP
MY_100_MAX_COLS = 2  # painter constant — not a Spec knob
MY_100_NUM_W = 8.0
MY_100_CHECK = 2.4
MY_100_CHECK_GAP = 1.6
MY_100_WRITE_GAP = 1.2
MY_100_DASH = 0.40
MY_100_DASH_GAP = 0.32


def _my_100_fill_rows(max_rows: int, entries: int) -> int:
    """Largest row count that leaves remainder as full columns (e.g. 20 → 40+40+20)."""
    for n_rows in range(max_rows, 0, -1):
        if entries % n_rows == 0:
            return n_rows
    return max_rows


def my_100_grid(well: Rect) -> tuple[int, int]:
    """Two equal columns. Rows from the well, preferring a full-column remainder."""
    n_cols = max(
        1,
        int((well.w + MY_100_COL_GAP) / (MY_100_MIN_COL_W + MY_100_COL_GAP)),
    )
    n_cols = min(n_cols, MY_100_MAX_COLS)
    max_rows = max(1, int(well.h / MY_100_MIN_ROW_H))
    return n_cols, _my_100_fill_rows(max_rows, MY_100_COUNT)


def my_100_capacity(well: Rect) -> int:
    cols, row_n = my_100_grid(well)
    return max(1, cols * row_n)


def my_100_row_h(well: Rect) -> float:
    _cols, row_n = my_100_grid(well)
    return well.h / row_n


def my_100_columns(well: Rect) -> tuple[Rect, ...]:
    """Same column tracks on every page — width does not change mid-book."""
    n_cols, _n_rows = my_100_grid(well)
    return columns(well, n_cols, gap=MY_100_COL_GAP)


def my_100_row_parts(row: Rect) -> tuple[Rect, Rect, Rect]:
    """Number stub, write-in, dashed checkbox — checkbox hugs the row end."""
    num, rest = row.split_left(MY_100_NUM_W)
    write_w = max(rest.w - MY_100_CHECK_GAP - MY_100_CHECK, 1.0)
    write = Rect(rest.x + MY_100_WRITE_GAP, rest.y, write_w - MY_100_WRITE_GAP, rest.h)
    check = Rect(row.right - MY_100_CHECK, rest.y, MY_100_CHECK, rest.h)
    return num, write, check


def my_100_page_count(well: Rect, *, entries: int = MY_100_COUNT) -> int:
    """How many pages the device well needs to seat ``entries`` at two columns."""
    per = my_100_capacity(well)
    return max(1, (max(entries, 0) + per - 1) // per)


def my_100_page_numbers(
    well: Rect, page: int, *, entries: int = MY_100_COUNT
) -> tuple[int, ...]:
    """1-based entry numbers on this 1-based page (column-major fill)."""
    if page < 1:
        return ()
    per = my_100_capacity(well)
    start = (page - 1) * per + 1
    stop = min(entries, page * per)
    if start > entries or stop < start:
        return ()
    return tuple(range(start, stop + 1))


def my_100_open_seat(well: Rect, n_entries: int) -> Rect | None:
    """Unused column(s) as unmarked paper. None when the page fills both tracks."""
    tracks = my_100_columns(well)
    _cols, n_rows = my_100_grid(well)
    used = min(len(tracks), (max(n_entries, 0) + n_rows - 1) // n_rows) if n_rows else 0
    if used >= len(tracks):
        return None
    first = tracks[used]
    last = tracks[-1]
    return Rect(first.x, well.y, last.right - first.x, well.h)


def _paint_dashed_rect(plotter: Plotter, box: Rect) -> None:
    """Small dashed checkbox — four perforated sides, not a solid tick."""
    _paint_perforation(
        plotter,
        box.x,
        box.y,
        box.right,
        box.y,
        dash=MY_100_DASH,
        gap=MY_100_DASH_GAP,
    )
    _paint_perforation(
        plotter,
        box.right,
        box.y,
        box.right,
        box.bottom,
        dash=MY_100_DASH,
        gap=MY_100_DASH_GAP,
    )
    _paint_perforation(
        plotter,
        box.right,
        box.bottom,
        box.x,
        box.bottom,
        dash=MY_100_DASH,
        gap=MY_100_DASH_GAP,
    )
    _paint_perforation(
        plotter,
        box.x,
        box.bottom,
        box.x,
        box.y,
        dash=MY_100_DASH,
        gap=MY_100_DASH_GAP,
    )


def _paint_my_100_row(plotter: Plotter, row: Rect, number: int) -> None:
    num, write, check = my_100_row_parts(row)
    _ink_text(
        plotter,
        num,
        f"{number}.",
        TypeRef(step="micro"),
        gray=MUTED,
        align="right",
    )
    rule_y = write.y + write.h * 0.72
    plotter.line(
        write.x,
        rule_y,
        write.right,
        rule_y,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )
    mark = Rect(
        check.x,
        rule_y - MY_100_CHECK,
        MY_100_CHECK,
        MY_100_CHECK,
    )
    _paint_dashed_rect(plotter, mark)


def paint_my_100(
    plotter: Plotter, box: Rect, page: My100Page, *, ramp: TypeRamp | None = None
) -> None:
    """Two equal columns of numbered write-ins. Unused last-page track stays blank."""
    _bound_ramp(plotter, ramp)
    tracks = my_100_columns(box)
    _n_cols, n_rows = my_100_grid(box)
    cells = [row for col in tracks for row in rows(col, n_rows, gap=0)]
    for cell, number in zip(cells, page.numbers, strict=False):
        _paint_my_100_row(plotter, cell, number)


# Optional Favorites well — 2×3 ranking cards. Sealed.
# No page-local title/caption band — well height goes to the cards.
FAVORITES_COLS = 2
FAVORITES_GRID_ROWS = 3
FAVORITES_CARD_GAP = 3.2
FAVORITES_INSET = 1.2
FAVORITES_HEAD_H = 9.0
FAVORITES_SLASH_W = 6.0
FAVORITES_ICON_W = 26.0
FAVORITES_ICON_GAP = 1.8
FAVORITES_ICON_SCALE = 0.74
FAVORITES_ICON_STROKE = 0.24
FAVORITES_ROW_H = 7.2
# Box / line / box / line / box — even optical weight across the strip.
FAVORITES_ICONS = ("camera", "note", "book", "utensils", "bag")


def favorites_seats(well: Rect) -> tuple[Rect, ...]:
    """Six equal ranking cards in a 2×3 grid. No title/caption band above."""
    cards: list[Rect] = []
    for band in rows(well, FAVORITES_GRID_ROWS, gap=FAVORITES_CARD_GAP):
        cards.extend(columns(band, FAVORITES_COLS, gap=FAVORITES_CARD_GAP))
    return tuple(cards)


def favorites_card_parts(card: Rect) -> tuple[Rect, Rect]:
    """Single three-cell header over a lined write-in well."""
    return card.split_top(min(FAVORITES_HEAD_H, card.h * 0.28))


def favorites_header_parts(header: Rect) -> tuple[Rect, Rect, Rect]:
    """One row: slash | name | icons. Same y, same h."""
    inner = header.inset(FAVORITES_INSET, 0.8)
    slash, rest = inner.split_left(min(FAVORITES_SLASH_W, inner.w * 0.16))
    icon_w = min(FAVORITES_ICON_W, rest.w * 0.58)
    name, icons = rest.split_left(rest.w - icon_w)
    return slash, name, icons


def favorites_body_rows(body: Rect) -> tuple[Rect, ...]:
    """Full-width write-in rows. No slash column."""
    inner = Rect(
        body.x + FAVORITES_INSET,
        body.y + 0.8,
        body.w - 2 * FAVORITES_INSET,
        max(body.h - FAVORITES_INSET - 0.8, FAVORITES_ROW_H),
    )
    n = max(1, int(inner.h / FAVORITES_ROW_H))
    return rows(inner, n)


def paint_favorites(
    plotter: Plotter, box: Rect, _page: FavoritesPage, *, ramp: TypeRamp | None = None
) -> None:
    """2×3 framed ranking cards — `/` | name | icons, then write-ins."""
    ramp = _bound_ramp(plotter, ramp)
    for card in favorites_seats(box):
        _paint_favorites_card(plotter, card)


def _paint_favorites_card(plotter: Plotter, card: Rect) -> None:
    header, body = favorites_card_parts(card)
    _wash(plotter, header, WASH)
    plotter.rect(card, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    slash, name, icons = favorites_header_parts(header)
    _ink_text(
        plotter,
        slash,
        "/",
        TypeRef(step="label"),
        gray=MUTED,
        align="center",
    )
    plotter.line(
        name.x + 0.4,
        name.y + name.h * 0.72,
        name.right - 0.4,
        name.y + name.h * 0.72,
        stroke_width=RULE,
        stroke_gray=MUTED,
    )
    _paint_favorites_icons(plotter, icons)
    plotter.line(
        card.x,
        header.bottom,
        card.right,
        header.bottom,
        stroke_width=HAIR,
        stroke_gray=INK,
    )
    for row in favorites_body_rows(body):
        plotter.line(
            row.x,
            row.y + row.h * 0.72,
            row.right,
            row.y + row.h * 0.72,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )


def _paint_favorites_icons(plotter: Plotter, box: Rect) -> None:
    slots = columns(box, len(FAVORITES_ICONS), gap=FAVORITES_ICON_GAP)
    mark = min(min(slot.h, slot.w) for slot in slots) * FAVORITES_ICON_SCALE
    for slot, kind in zip(slots, FAVORITES_ICONS, strict=True):
        icon = Rect(
            slot.x + (slot.w - mark) / 2,
            slot.y + (slot.h - mark) / 2,
            mark,
            mark,
        )
        _paint_favorites_icon(plotter, icon, kind)


def _paint_favorites_icon(plotter: Plotter, box: Rect, kind: str) -> None:
    match kind:
        case "camera":
            _fav_icon_camera(plotter, box)
        case "book":
            _fav_icon_book(plotter, box)
        case "note":
            _fav_icon_note(plotter, box)
        case "utensils":
            _fav_icon_utensils(plotter, box)
        case "bag":
            _fav_icon_bag(plotter, box)
        case _:
            raise ValueError(f"unknown favorites icon {kind!r}")


def _fav_stroke(plotter: Plotter, x1: float, y1: float, x2: float, y2: float) -> None:
    plotter.line(x1, y1, x2, y2, stroke_width=FAVORITES_ICON_STROKE, stroke_gray=INK)


def _fav_box(plotter: Plotter, box: Rect) -> None:
    plotter.rect(
        box,
        stroke=True,
        fill=False,
        stroke_width=FAVORITES_ICON_STROKE,
        stroke_gray=INK,
    )


def _fav_icon_camera(plotter: Plotter, box: Rect) -> None:
    """Movie camera — twin reels, body, barrel. Not a nested frame."""
    reel = min(box.w, box.h) * 0.28
    top = box.y + box.h * 0.08
    left = Rect(box.x + box.w * 0.10, top, reel, reel)
    right = Rect(box.x + box.w * 0.46, top, reel, reel)
    _fav_box(plotter, left)
    _fav_box(plotter, right)
    body_top = left.bottom + box.h * 0.06
    body = Rect(box.x + box.w * 0.08, body_top, box.w * 0.58, box.h * 0.46)
    _fav_box(plotter, body)
    lens_h = body.h * 0.58
    lens = Rect(
        body.right,
        body.y + (body.h - lens_h) / 2,
        box.w * 0.22,
        lens_h,
    )
    _fav_box(plotter, lens)


def _fav_icon_book(plotter: Plotter, box: Rect) -> None:
    page = Rect(box.x + box.w * 0.18, box.y + box.h * 0.10, box.w * 0.64, box.h * 0.80)
    _fav_box(plotter, page)
    spine = page.x + page.w * 0.34
    _fav_stroke(plotter, spine, page.y, spine, page.bottom)


def _fav_icon_note(plotter: Plotter, box: Rect) -> None:
    """Eighth-note stand-in — head, stem, two flags for upper mass."""
    head = Rect(box.x + box.w * 0.08, box.y + box.h * 0.52, box.w * 0.54, box.h * 0.40)
    _fav_box(plotter, head)
    stem_x = head.right
    top = box.y + box.h * 0.06
    _fav_stroke(plotter, stem_x, head.y + head.h * 0.10, stem_x, top)
    _fav_stroke(plotter, stem_x, top, box.x + box.w * 0.92, box.y + box.h * 0.24)
    _fav_stroke(
        plotter,
        stem_x,
        box.y + box.h * 0.18,
        box.x + box.w * 0.92,
        box.y + box.h * 0.36,
    )


def _fav_icon_utensils(plotter: Plotter, box: Rect) -> None:
    top = box.y + box.h * 0.08
    join = box.y + box.h * 0.42
    bot = box.bottom - box.h * 0.06
    for t in (0.12, 0.28, 0.44):
        x = box.x + box.w * t
        _fav_stroke(plotter, x, top, x, join)
    handle = box.x + box.w * 0.28
    _fav_stroke(plotter, box.x + box.w * 0.12, join, box.x + box.w * 0.44, join)
    _fav_stroke(plotter, handle, join, handle, bot)
    knife = box.x + box.w * 0.78
    _fav_stroke(plotter, knife, top, knife, bot)
    _fav_stroke(plotter, knife + box.w * 0.10, top, knife + box.w * 0.10, join)
    _fav_stroke(plotter, knife, top, knife + box.w * 0.10, top)


def _fav_icon_bag(plotter: Plotter, box: Rect) -> None:
    body = Rect(box.x + box.w * 0.14, box.y + box.h * 0.36, box.w * 0.72, box.h * 0.54)
    _fav_box(plotter, body)
    left = box.x + box.w * 0.34
    right = box.right - box.w * 0.34
    top = box.y + box.h * 0.12
    _fav_stroke(plotter, left, body.y, left, top)
    _fav_stroke(plotter, left, top, right, top)
    _fav_stroke(plotter, right, top, right, body.y)


PROJECT_CARD_GAP = 2.6
PROJECT_HEADER_H = 6.2
PROJECT_LEFT_GAP = 1.0
PROJECT_P = 5.0
PROJECT_STATUS_MARK = 3.2


def project_card_seats(well: Rect, cards: int) -> tuple[Rect, ...]:
    """One row track per project card."""
    return rows(well, cards, gap=PROJECT_CARD_GAP)


TICKET_GAP = 1.4
TICKET_STUB_W = 12.0
TICKET_INSET_X = 1.6
TICKET_INSET_Y = 1.1
TICKET_MARK = 5.6
TICKET_PERF_DASH = 0.52
TICKET_PERF_GAP = 0.40
TICKET_NAME_WEIGHTS = (0.55, 0.45)
TICKET_BODY_GAP = 1.8
TICKET_PREVIEW_GAP = 1.4
TICKET_PREVIEW_INSET = 0.35
TICKET_STRIP_PAD = 0.40
TICKET_STRIP_LEFT = 0.30
TICKET_STRIP_GRAY = RULE_C

# ``paint_project`` symbol strip — same marks, size, and strip height.
CLONE_ICON = 2.1
CLONE_STRIP_H = 2.8
CLONE_STRIP_COL_GAP = 1.05
CLONE_ICONS = (
    "triangle",
    "cross",
    "hexagon",
    "square",
    "crescent",
    "diamond",
    "circle",
    "plus",
    "star",
)
CLONE_SPINE_W = 1.4
CLONE_RAIL_GAP = 2.6
CLONE_RAIL_WEIGHTS = (0.76, 0.24)
CLONE_CARD_WEIGHTS = (0.50, 0.50)
CLONE_INSET_X = 1.6
CLONE_INSET_Y = 1.4
CLONE_COL_GAP = 3.4
CLONE_STAR = 2.0
CLONE_TRACK_H = 26.0
CLONE_RAIL_SLOT_GAP = 1.8
CLONE_STATUS_LABELS = ("Todo", "In Progress", "Done")
CLONE_P_PAD = 0.40
CLONE_P_CORNER = (2.15, 1.85)
CLONE_NAME_GAP = 1.4
CLONE_TASK_TOP = 0.4
CLONE_TASK_CLEAR = 0.55
CLONE_DOT_PITCH = 2.8
CLONE_DOT = 0.32


def project_ticket_seats(well: Rect, n: int) -> tuple[Rect, ...]:
    """Equal stacked ticket rows filling the well."""
    return rows(well, n, gap=TICKET_GAP)


def project_ticket_parts(ticket: Rect) -> tuple[Rect, Rect]:
    """Stub | title body, after a quiet inset."""
    inner = ticket.inset(TICKET_INSET_X, TICKET_INSET_Y)
    return inner.split_left(TICKET_STUB_W)


def project_ticket_body_seats(body: Rect) -> tuple[Rect, Rect]:
    """Write-in name | dest-card preview (~0.45 of the body so boxes read)."""
    return columns(body, 2, gap=TICKET_BODY_GAP, weights=TICKET_NAME_WEIGHTS)


def project_ticket_preview_cards(preview: Rect, cards: int) -> tuple[Rect, ...]:
    """``paint_project`` dest cards, side-by-side thumbnail — hairline open frames.

    ``cards`` is the dest stack count (2–4). Frames share the same preview
    pocket width as the historical 3-square row; they shrink horizontally
    to fit N and stay evenly spaced.
    """
    pocket = preview.inset(TICKET_PREVIEW_INSET, TICKET_PREVIEW_INSET)
    return columns(pocket, cards, gap=TICKET_PREVIEW_GAP)


def project_ticket_name_seats(name: Rect) -> tuple[Rect, Rect]:
    """Write-in band over the ``paint_project`` 9-mark strip. Hline sits at the band bottom."""
    block = CLONE_STRIP_H + TICKET_STRIP_PAD
    write_h = max(name.h - block, 1)
    write = Rect(name.x, name.y, name.w, write_h)
    strip = Rect(
        name.x + TICKET_STRIP_LEFT,
        write.bottom + TICKET_STRIP_PAD,
        name.w - TICKET_STRIP_LEFT,
        CLONE_STRIP_H,
    )
    return write, strip


def project_ticket_link_hits(ticket: Rect, cards: int) -> tuple[Rect, ...]:
    """Stub column + each preview card. Write-in and symbol strip stay unlinkable."""
    stub, body = project_ticket_parts(ticket)
    _, preview = project_ticket_body_seats(body)
    return (stub, *project_ticket_preview_cards(preview, cards))


def paint_projects_index(
    plotter: Plotter, box: Rect, index: ProjectsIndex, *, ramp: TypeRamp | None = None
) -> None:
    """``ProjectsIndex`` — stub, raised write-in, symbol strip, N-card preview; stub + preview links."""
    ramp = _bound_ramp(plotter, ramp)
    for seat, ticket in zip(
        project_ticket_seats(box, len(index.tickets)), index.tickets, strict=True
    ):
        _paint_project_ticket(plotter, seat, ticket, cards=index.cards, ramp=ramp)
        for hit in project_ticket_link_hits(seat, index.cards):
            plotter.link(hit, ticket.dest)


def _paint_project_ticket(
    plotter: Plotter,
    box: Rect,
    ticket: ProjectTicket,
    *,
    cards: int,
    ramp: TypeRamp,
) -> None:
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    stub, body = project_ticket_parts(box)
    name, preview = project_ticket_body_seats(body)
    write, strip = project_ticket_name_seats(name)
    mark_y = stub.y + (stub.h - TICKET_MARK) / 2
    mark = Rect(stub.x + (stub.w - TICKET_MARK) / 2, mark_y, TICKET_MARK, TICKET_MARK)
    plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    _ink_text(
        plotter,
        mark,
        f"{ticket.number:02d}",
        TypeRef(step="label", emphasis="strong"),
        gray=INK,
        align="center",
    )
    perf_x = stub.right + 0.55
    _paint_perforation(plotter, perf_x, box.y + 0.9, perf_x, box.bottom - 0.9)
    plotter.line(
        write.x,
        write.bottom,
        write.right,
        write.bottom,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )
    _paint_clone_icon_strip(plotter, strip)
    for card in project_ticket_preview_cards(preview, cards):
        plotter.rect(card, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    _paint_perforation(plotter, box.x + 1.4, box.bottom, box.right - 1.4, box.bottom)


def _paint_perforation(
    plotter: Plotter,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    dash: float = TICKET_PERF_DASH,
    gap: float = TICKET_PERF_GAP,
) -> None:
    """Thin dashed hairline — ticket tear, not a solid rule."""
    dx = x2 - x1
    dy = y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 0:
        return
    ux, uy = dx / length, dy / length
    walked = 0.0
    while walked < length:
        start = walked
        stop = min(walked + dash, length)
        plotter.line(
            x1 + ux * start,
            y1 + uy * start,
            x1 + ux * stop,
            y1 + uy * stop,
            stroke_width=HAIR,
            stroke_gray=INK,
        )
        walked = stop + gap


def clone_task_count(box: Rect) -> int:
    """Focus rows that fill ``box``, with clearance above the symbol strip."""
    usable = box.h - CLONE_TASK_TOP - CLONE_TASK_CLEAR
    if usable < TICK:
        return 1
    return max(1, int((usable - TICK) / FOCUS_PITCH) + 1)


def projects_clone_a_name_field(header: Rect) -> tuple[Rect, Rect]:
    """P square and the bordered name field beside it."""
    y = header.y + (header.h - PROJECT_P) / 2
    mark = Rect(header.x, y, PROJECT_P, PROJECT_P)
    field = Rect(
        mark.right + CLONE_NAME_GAP,
        y,
        max(header.right - mark.right - CLONE_NAME_GAP, 1),
        PROJECT_P,
    )
    return mark, field


def projects_clone_a_well(well: Rect) -> tuple[Rect, Rect]:
    """Board column | status rail — kanban’s right-hand track, Nomad-narrow."""
    return columns(well, 2, gap=CLONE_RAIL_GAP, weights=CLONE_RAIL_WEIGHTS)


def projects_clone_a_seats(
    well: Rect, cards: int
) -> tuple[tuple[Rect, ...], tuple[Rect, ...]]:
    """Stacked project cards and the matching three-stage rail seats."""
    board, rail = projects_clone_a_well(well)
    return project_card_seats(board, cards), rows(rail, cards, gap=PROJECT_CARD_GAP)


def projects_clone_a_card(card: Rect) -> tuple[Rect, Rect, Rect, Rect, Rect, Rect]:
    """spine, header, name field, tasks, notes (full right), icon strip (left)."""
    spine = Rect(card.x, card.y, CLONE_SPINE_W, card.h)
    body = Rect(card.x + CLONE_SPINE_W, card.y, card.w - CLONE_SPINE_W, card.h).inset(
        CLONE_INSET_X, CLONE_INSET_Y
    )
    left, notes = columns(body, 2, gap=CLONE_COL_GAP, weights=CLONE_CARD_WEIGHTS)
    name_h, left_rest = left.split_top(PROJECT_HEADER_H)
    _, name_field = projects_clone_a_name_field(name_h)
    mid = Rect(
        left_rest.x,
        left_rest.y + PROJECT_LEFT_GAP,
        left_rest.w,
        left_rest.h - PROJECT_LEFT_GAP,
    )
    tasks, strip = rows(
        mid,
        2,
        gap=PROJECT_LEFT_GAP,
        weights=(mid.h - CLONE_STRIP_H - PROJECT_LEFT_GAP, CLONE_STRIP_H),
    )
    return spine, name_h, name_field, tasks, notes, strip


def paint_project(
    plotter: Plotter, box: Rect, board: ProjectsBoard, *, ramp: TypeRamp | None = None
) -> None:
    """``ProjectsBoard`` well — spine, soft P + name box, ticks, 2.8 mm dots, strip, status rail."""
    _bound_ramp(plotter, ramp)
    cards, rails = projects_clone_a_seats(box, board.cards)
    _wash(plotter, projects_clone_a_well(box)[1], WASH)
    for card, rail in zip(cards, rails, strict=True):
        spine, name_h, name_field, tasks, notes, strip = projects_clone_a_card(card)
        plotter.rect(spine, stroke=False, fill=True, fill_gray=INK)
        _paint_clone_priority(plotter, name_h)
        plotter.rect(
            name_field, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK
        )
        _paint_clone_tasks(plotter, tasks)
        _paint_clone_dotgrid(plotter, notes)
        _paint_clone_icon_strip(plotter, strip)
        _paint_clone_status_track(plotter, rail)
        plotter.rect(card, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)


def paint_dotgrid(plotter: Plotter, box: Rect) -> None:
    """RULE_C dots on tracks at ``CLONE_DOT_PITCH``. No pocket frame."""
    nx = max(2, int(box.w / CLONE_DOT_PITCH))
    ny = max(2, int(box.h / CLONE_DOT_PITCH))
    for band in rows(box, ny):
        for cell in columns(band, nx):
            plotter.rect(
                Rect(
                    cell.x + (cell.w - CLONE_DOT) / 2,
                    cell.y + (cell.h - CLONE_DOT) / 2,
                    CLONE_DOT,
                    CLONE_DOT,
                ),
                stroke=False,
                fill=True,
                fill_gray=RULE_C,
            )


def _paint_clone_dotgrid(plotter: Plotter, box: Rect) -> None:
    """E-ink dot grid — SOFT pocket, RULE_C dots on tracks at note pitch."""
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    inset = Rect(box.x + 1.1, box.y + 1.2, box.w - 2.2, box.h - 2.4)
    paint_dotgrid(plotter, inset)


def _paint_clone_priority(plotter: Plotter, header: Rect) -> float:
    """P-box: muted corner-fraction label, leftover is write-in. Clone only."""
    mark, _field = projects_clone_a_name_field(header)
    plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    cw, ch = CLONE_P_CORNER
    _ink_text(
        plotter,
        Rect(mark.x + CLONE_P_PAD, mark.y + CLONE_P_PAD, cw, ch),
        "P",
        TypeRef(step="caption"),
        gray=MUTED,
        align="left",
        small_caps=True,
    )
    return mark.bottom


def _paint_clone_tasks(plotter: Plotter, box: Rect) -> None:
    count = clone_task_count(box)
    y = box.y + CLONE_TASK_TOP
    star_right = box.right - CLONE_STAR - 1.0
    for _ in range(count):
        _paint_focus_row(plotter, box.x, y, star_right)
        star = Rect(
            box.right - CLONE_STAR,
            y + (TICK - CLONE_STAR) / 2,
            CLONE_STAR,
            CLONE_STAR,
        )
        _paint_diamond(plotter, star)
        y += FOCUS_PITCH


def _paint_clone_status_track(plotter: Plotter, box: Rect) -> None:
    """Vertical Todo → In Progress → Done. Squares stand in for circles."""
    track_h = min(CLONE_TRACK_H, box.h - 2.0)
    track = Rect(box.x, box.y + (box.h - track_h) / 2, box.w, track_h)
    inset = track.inset(1.4, 0.6)
    marks: list[Rect] = []
    for slot, label in zip(
        rows(inset, 3, gap=CLONE_RAIL_SLOT_GAP), CLONE_STATUS_LABELS, strict=True
    ):
        mark_y = slot.y + (slot.h - PROJECT_STATUS_MARK) / 2
        mark = Rect(slot.x, mark_y, PROJECT_STATUS_MARK, PROJECT_STATUS_MARK)
        plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
        _ink_text(
            plotter,
            Rect(
                mark.right + 0.7, slot.y, max(slot.right - mark.right - 0.7, 1), slot.h
            ),
            label,
            TypeRef(step="caption"),
            gray=MUTED,
            small_caps=True,
            align="left",
        )
        marks.append(mark)
    cx = marks[0].x + marks[0].w / 2
    for above, below in zip(marks, marks[1:]):
        plotter.line(cx, above.bottom, cx, below.y, stroke_width=HAIR, stroke_gray=INK)


def _paint_diamond(plotter: Plotter, box: Rect, *, stroke_width: float = HAIR) -> None:
    """Open rhombus — never filled. Check-off milestones pass a heavier stroke."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    plotter.line(cx, box.y, box.right, cy, stroke_width=stroke_width, stroke_gray=INK)
    plotter.line(
        box.right, cy, cx, box.bottom, stroke_width=stroke_width, stroke_gray=INK
    )
    plotter.line(cx, box.bottom, box.x, cy, stroke_width=stroke_width, stroke_gray=INK)
    plotter.line(box.x, cy, cx, box.y, stroke_width=stroke_width, stroke_gray=INK)


def _stroke_circle(plotter: Plotter, box: Rect) -> None:
    """Hairline ellipse inscribed in ``box``. Plotter has no native ellipse."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    rx = box.w / 2
    ry = box.h / 2
    n = CHECKOFF_CIRCLE_SEGS
    pts = [
        (
            cx + rx * math.cos(math.tau * i / n),
            cy + ry * math.sin(math.tau * i / n),
        )
        for i in range(n)
    ]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1], strict=True):
        plotter.line(x1, y1, x2, y2, stroke_width=HAIR, stroke_gray=INK)


def _paint_clone_icon_strip(plotter: Plotter, box: Rect) -> None:
    """Filled icons, even spread — same craft as the ``paint_project`` card strip."""
    slots = columns(box, len(CLONE_ICONS), gap=CLONE_STRIP_COL_GAP)
    for slot, kind in zip(slots, CLONE_ICONS, strict=True):
        s = min(CLONE_ICON, slot.h - 0.2, slot.w)
        icon = Rect(slot.x + (slot.w - s) / 2, slot.y + (slot.h - s) / 2, s, s)
        _paint_clone_icon(plotter, icon, kind)


def _paint_clone_icon(plotter: Plotter, box: Rect, kind: str) -> None:
    match kind:
        case "square":
            plotter.rect(box, stroke=False, fill=True, fill_gray=TICKET_STRIP_GRAY)
        case "plus":
            arm = 0.30
            plotter.rect(
                Rect(box.x + box.w * (1 - arm) / 2, box.y, box.w * arm, box.h),
                stroke=False,
                fill=True,
                fill_gray=TICKET_STRIP_GRAY,
            )
            plotter.rect(
                Rect(box.x, box.y + box.h * (1 - arm) / 2, box.w, box.h * arm),
                stroke=False,
                fill=True,
                fill_gray=TICKET_STRIP_GRAY,
            )
        case "circle":
            _fill_circle(plotter, box)
        case "diamond":
            _fill_diamond(plotter, box)
        case "triangle":
            _fill_triangle(plotter, box)
        case "crescent":
            _fill_crescent(plotter, box)
        case "hexagon":
            _fill_hexagon(plotter, box)
        case "cross":
            _fill_cross(plotter, box)
        case "star":
            _fill_star(plotter, box)
        case _:
            raise ValueError(f"unknown clone icon {kind!r}")


def _scan_box(box: Rect, *, n: int = 11) -> tuple[list[float], float]:
    dy = box.h / n
    return [box.y + (i + 0.5) * dy for i in range(n)], dy


def _fill_circle(plotter: Plotter, box: Rect) -> None:
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    rx = box.w / 2
    ry = box.h / 2
    ys, dy = _scan_box(box)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        t = (y - cy) / ry
        if abs(t) >= 1:
            continue
        half = rx * math.sqrt(max(0.0, 1.0 - t * t))
        spans.append((y - dy / 2, cx - half, cx + half))
    _fill_span_rows(plotter, spans, dy)


def _fill_diamond(plotter: Plotter, box: Rect) -> None:
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    rx = box.w / 2
    ry = box.h / 2
    ys, dy = _scan_box(box)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        t = abs((y - cy) / ry)
        if t >= 1:
            continue
        half = rx * (1.0 - t)
        spans.append((y - dy / 2, cx - half, cx + half))
    _fill_span_rows(plotter, spans, dy)


def _fill_triangle(plotter: Plotter, box: Rect) -> None:
    """Point-up triangle inscribed in ``box``."""
    ys, dy = _scan_box(box)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        t = (y - box.y) / box.h
        half = (box.w / 2) * t
        cx = box.x + box.w / 2
        spans.append((y - dy / 2, cx - half, cx + half))
    _fill_span_rows(plotter, spans, dy)


def _fill_poly(
    plotter: Plotter, box: Rect, pts: list[tuple[float, float]], *, n: int = 12
) -> None:
    ys, dy = _scan_box(box, n=n)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        xs = _poly_xs_at(pts, y)
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            spans.append((y - dy / 2, xs[i], xs[i + 1]))
    _fill_span_rows(plotter, spans, dy)


def _fill_crescent(plotter: Plotter, box: Rect) -> None:
    """Waxing crescent — outer disc minus an offset disc. Distinct from circle."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    rx = box.w / 2
    ry = box.h / 2
    ox = cx + rx * 0.36
    r2x = rx * 0.78
    r2y = ry * 0.78
    ys, dy = _scan_box(box, n=13)
    spans: list[tuple[float, float, float]] = []
    for y in ys:
        t = (y - cy) / ry
        if abs(t) >= 1:
            continue
        half = rx * math.sqrt(max(0.0, 1.0 - t * t))
        left, right = cx - half, cx + half
        t2 = (y - cy) / r2y
        if abs(t2) < 1:
            cut = r2x * math.sqrt(max(0.0, 1.0 - t2 * t2))
            cut_l, cut_r = ox - cut, ox + cut
            if cut_l <= left < cut_r < right:
                left = cut_r
            elif left < cut_l < right <= cut_r:
                right = cut_l
            elif cut_l <= left and right <= cut_r:
                continue
        if right - left > 0.08:
            spans.append((y - dy / 2, left, right))
    _fill_span_rows(plotter, spans, dy)


def _fill_hexagon(plotter: Plotter, box: Rect) -> None:
    """Pointy-top hexagon — distinct from square and diamond."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    r = min(box.w, box.h) / 2
    pts = [
        (
            cx + r * math.cos(math.radians(-90 + i * 60)),
            cy + r * math.sin(math.radians(-90 + i * 60)),
        )
        for i in range(6)
    ]
    _fill_poly(plotter, box, pts)


def _fill_cross(plotter: Plotter, box: Rect) -> None:
    """X — two thick diagonals. Distinct from plus and from the 5-point star."""
    t = min(box.w, box.h) * 0.22
    x0, y0, x1, y1 = box.x, box.y, box.right, box.bottom
    _fill_poly(plotter, box, [(x0 + t, y0), (x1, y1 - t), (x1 - t, y1), (x0, y0 + t)])
    _fill_poly(plotter, box, [(x1 - t, y0), (x1, y0 + t), (x0 + t, y1), (x0, y1 - t)])


def _fill_star(plotter: Plotter, box: Rect) -> None:
    """Five-point star — same as ``paint_project``."""
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    r = min(box.w, box.h) / 2
    _fill_poly(plotter, box, _star_poly(cx, cy, r), n=13)


def _star_poly(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    r_in = r * 0.38
    pts: list[tuple[float, float]] = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rad = r if i % 2 == 0 else r_in
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pts


def _poly_xs_at(pts: list[tuple[float, float]], y: float) -> list[float]:
    xs: list[float] = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            if y1 != y0:
                xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    return xs


def _fill_span_rows(
    plotter: Plotter, spans: list[tuple[float, float, float]], dy: float
) -> None:
    for y, x0, x1 in spans:
        if x1 - x0 > 0.08:
            plotter.rect(
                Rect(x0, y, x1 - x0, dy),
                stroke=False,
                fill=True,
                fill_gray=TICKET_STRIP_GRAY,
            )


MEET_GAP = 2.6
MEET_HEAD_INSET_X = 1.8
MEET_HEAD_INSET_Y = 1.2
MEET_HEAD_LINE_H = 5.4
MEET_HEAD_COL_GAP = 2.8
MEET_HEAD_WEIGHTS = (0.64, 0.36)
MEET_LABEL_W = 12.0
MEET_WRITE_LABEL_H = 3.8

MEET_INDEX_GAP = 1.0
MEET_INDEX_INSET_X = 1.2
MEET_INDEX_INSET_Y = 0.7
MEET_INDEX_STUB_W = 9.6
MEET_INDEX_STUB_GAP = 1.6
MEET_INDEX_MARK = 5.0
MEET_INDEX_COL_GAP = 2.8
MEET_INDEX_WEIGHTS = (0.22, 0.78)
MEET_INDEX_DATE_LABEL_W = 8.0


def meeting_head_height() -> float:
    """One-line title|date band — not two stacked write-ins."""
    return MEET_HEAD_INSET_Y * 2 + MEET_HEAD_LINE_H


def _below(box: Rect, gap: float) -> Rect:
    return Rect(box.x, box.y + gap, box.w, box.h - gap)


def meeting_seats(
    well: Rect, agenda: int, action_items: int
) -> tuple[Rect, Rect, Rect, Rect]:
    """Head, agenda, leftover notes, action items. Notes flex."""
    head, rest = well.split_top(meeting_head_height())
    leftover = _below(rest, MEET_GAP)
    agenda_h = checklist_content_height(agenda)
    agenda_box, rest = leftover.split_top(agenda_h)
    leftover = _below(rest, MEET_GAP)
    action_h = checklist_content_height(action_items)
    notes_h = max(leftover.h - action_h - MEET_GAP, 1)
    notes, action_box = rows(leftover, 2, gap=MEET_GAP, weights=(notes_h, action_h))
    return head, agenda_box, notes, action_box


def meeting_head_seats(head: Rect) -> tuple[Rect, Rect]:
    """Title write-in | Date write-in on one horizontal row."""
    inner = head.inset(MEET_HEAD_INSET_X, MEET_HEAD_INSET_Y)
    return columns(inner, 2, gap=MEET_HEAD_COL_GAP, weights=MEET_HEAD_WEIGHTS)


def paint_meeting(
    plotter: Plotter, box: Rect, agenda: MeetingAgenda, *, ramp: TypeRamp | None = None
) -> None:
    """Locked Meeting dest — title|date, agenda, notes, action items."""
    ramp = _bound_ramp(plotter, ramp)
    head, agenda_box, notes, action_items = meeting_seats(
        box, agenda.agenda, agenda.action_items
    )
    _paint_meeting_head(plotter, head)
    _paint_checklist_box(
        plotter, agenda_box, label="Agenda", rows=agenda.agenda, ramp=ramp
    )
    _paint_note_box(plotter, notes, label="Notes", ramp=ramp)
    _paint_checklist_box(
        plotter, action_items, label="Action items", rows=agenda.action_items, ramp=ramp
    )


def _paint_meeting_head(plotter: Plotter, head: Rect) -> None:
    plotter.rect(head, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    title, dated = meeting_head_seats(head)
    _paint_meeting_writein(plotter, title, "Title")
    _paint_meeting_writein(plotter, dated, "Date")


def _paint_meeting_writein(plotter: Plotter, box: Rect, label: str) -> None:
    """Label and underline share a baseline — rule sits just under the scaps."""
    tag, write = box.split_left(MEET_LABEL_W)
    rule_y = box.bottom
    label_box = Rect(tag.x, rule_y - MEET_WRITE_LABEL_H, tag.w, MEET_WRITE_LABEL_H)
    _ink_text(
        plotter,
        label_box,
        label,
        TypeRef(step="label"),
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    plotter.line(
        write.x, rule_y, write.right, rule_y, stroke_width=RULE, stroke_gray=RULE_C
    )


def meetings_index_roster(box: Rect, n: int) -> tuple[Rect, ...]:
    """Equal stacked roster rows filling the well."""
    return rows(box, n, gap=MEET_INDEX_GAP)


def meeting_index_row_parts(row: Rect) -> tuple[Rect, Rect]:
    """Stub | date+title body, after a quiet inset and stub gap."""
    inner = row.inset(MEET_INDEX_INSET_X, MEET_INDEX_INSET_Y)
    stub, rest = inner.split_left(MEET_INDEX_STUB_W)
    body = Rect(
        rest.x + MEET_INDEX_STUB_GAP, rest.y, rest.w - MEET_INDEX_STUB_GAP, rest.h
    )
    return stub, body


def meeting_index_row_seats(row: Rect) -> tuple[Rect, Rect]:
    """Date cue | title write-in on the body. Stub is not a write-in."""
    _, body = meeting_index_row_parts(row)
    return columns(body, 2, gap=MEET_INDEX_COL_GAP, weights=MEET_INDEX_WEIGHTS)


def meeting_index_link_hits(row: Rect) -> tuple[Rect, ...]:
    """Stub column only. Date and title write-ins stay unlinkable."""
    stub, _body = meeting_index_row_parts(row)
    return (stub,)


def paint_meetings_index(
    plotter: Plotter, box: Rect, index: MeetingIndex, *, ramp: TypeRamp | None = None
) -> None:
    """``MeetingIndex`` — dense dated roster. Stub is the dest hit; write-ins stay unlinkable."""
    _bound_ramp(plotter, ramp)
    for seat, slot in zip(
        meetings_index_roster(box, len(index.slots)), index.slots, strict=True
    ):
        _paint_meeting_index_row(plotter, seat, slot.number)
        for hit in meeting_index_link_hits(seat):
            plotter.link(hit, slot.dest)


def _paint_meeting_index_row(plotter: Plotter, box: Rect, number: int) -> None:
    """Slot stub + date cue + title write-in/rule on one baseline."""
    stub, _body = meeting_index_row_parts(box)
    _paint_meeting_index_stub(plotter, stub, number)
    dated, title = meeting_index_row_seats(box)
    _paint_meeting_index_date_cue(plotter, dated)
    _paint_meeting_index_title(plotter, title)


def _paint_meeting_index_stub(plotter: Plotter, stub: Rect, number: int) -> None:
    """Hairline slot mark — the visible tap target, same as ``paint_projects_index`` stubs."""
    mark_y = stub.y + (stub.h - MEET_INDEX_MARK) / 2
    mark = Rect(
        stub.x + (stub.w - MEET_INDEX_MARK) / 2,
        mark_y,
        MEET_INDEX_MARK,
        MEET_INDEX_MARK,
    )
    plotter.rect(mark, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    _ink_text(
        plotter,
        mark,
        f"{number:02d}",
        TypeRef(step="label", emphasis="strong"),
        gray=INK,
        align="center",
    )


def _paint_meeting_index_date_cue(plotter: Plotter, box: Rect) -> None:
    """Muted Date label + short write-in — the date cue, not a printed calendar."""
    tag, write = box.split_left(MEET_INDEX_DATE_LABEL_W)
    rule_y = box.bottom
    _ink_text(
        plotter,
        Rect(tag.x, rule_y - MEET_WRITE_LABEL_H, tag.w, MEET_WRITE_LABEL_H),
        "Date",
        TypeRef(step="caption"),
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    plotter.line(
        write.x, rule_y, write.right, rule_y, stroke_width=RULE, stroke_gray=RULE_C
    )


def _paint_meeting_index_title(plotter: Plotter, box: Rect) -> None:
    """Title write-in rule on the same baseline as the date cue."""
    plotter.line(
        box.x, box.bottom, box.right, box.bottom, stroke_width=RULE, stroke_gray=RULE_C
    )


TASK_INDEX_BAND_GAP = 2.6
TASK_INDEX_INSET_X = 1.8
TASK_INDEX_INSET_Y = 1.4
TASK_INDEX_HEAD_H = 4.2
TASK_INDEX_HEAD_GAP = 0.8
TASK_INDEX_ROW_GAP = 1.0
TASK_INDEX_LINE_H = 5.4
TASK_INDEX_WEEK_W = 12.0
# Midpoint of original fat column (26) and hug (14.8).
TASK_INDEX_RANGE_W = 20.4
# Midpoint of original WRITE_GAP (2.8) and 4pt (1.41).
TASK_INDEX_WRITE_GAP = 2.105
TASK_GAP = 2.6
TASK_CHECKLIST_FRAC = 2 / 3


def tasks_index_bands(well: Rect, week_counts: tuple[int, ...]) -> tuple[Rect, ...]:
    """Month bands weighted by week-row count. Horizon scan, not equal status slices."""
    weights = tuple(float(max(1, count)) for count in week_counts)
    return rows(well, len(weights), gap=TASK_INDEX_BAND_GAP, weights=weights)


def tasks_index_band_seats(band: Rect, n: int) -> tuple[Rect, tuple[Rect, ...]]:
    """Month header over linked week rows, after a quiet inset."""
    inner = band.inset(TASK_INDEX_INSET_X, TASK_INDEX_INSET_Y)
    head, rest = inner.split_top(TASK_INDEX_HEAD_H)
    body = Rect(
        rest.x, rest.y + TASK_INDEX_HEAD_GAP, rest.w, rest.h - TASK_INDEX_HEAD_GAP
    )
    return head, rows(body, n, gap=TASK_INDEX_ROW_GAP)


def tasks_index_week_strip(row: Rect) -> Rect:
    """Content-height text+rule strip, vertically centered in the stretched week row."""
    h = min(TASK_INDEX_LINE_H, row.h)
    return Rect(row.x, row.y + (row.h - h) / 2, row.w, h)


def tasks_index_rule_y(row: Rect) -> float:
    """Write-in baseline — strip bottom, not the stretched row floor."""
    return tasks_index_week_strip(row).bottom


def tasks_index_week_parts(row: Rect) -> tuple[Rect, Rect, Rect]:
    """Wnn stub | printed range | write-in — ``tracks.columns``; gap only date→hline."""
    strip = tasks_index_week_strip(row)
    stub_w = TASK_INDEX_WEEK_W
    stub, rest = columns(strip, 2, gap=0, weights=(stub_w, max(strip.w - stub_w, 1)))
    range_w = TASK_INDEX_RANGE_W
    write_w = max(rest.w - TASK_INDEX_WRITE_GAP - range_w, 1)
    dated, write = columns(
        rest, 2, gap=TASK_INDEX_WRITE_GAP, weights=(range_w, write_w)
    )
    return stub, dated, write


def tasks_index_link_hits(row: Rect) -> tuple[Rect, ...]:
    """Stub + week range. Write-in hline stays unlinkable (same as ``paint_meetings_index`` / ``paint_projects_index``)."""
    stub, dated, _write = tasks_index_week_parts(row)
    return (stub, dated)


def paint_tasks_index(
    plotter: Plotter, box: Rect, index: TasksIndex, *, ramp: TypeRamp | None = None
) -> None:
    """``TasksIndex`` — month-banded week rows. Not Active/Waiting/Done, not This week/Later."""
    _bound_ramp(plotter, ramp)
    counts = tuple(len(band.weeks) for band in index.bands)
    for band_box, band in zip(tasks_index_bands(box, counts), index.bands, strict=True):
        plotter.rect(
            band_box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT
        )
        head, lines = tasks_index_band_seats(band_box, len(band.weeks))
        _ink_text(
            plotter,
            head,
            band.name,
            TypeRef(step="label", emphasis="strong"),
            gray=INK,
            small_caps=True,
            align="left",
        )
        plotter.line(
            head.x,
            head.bottom,
            head.right,
            head.bottom,
            stroke_width=HAIR,
            stroke_gray=SOFT,
        )
        for line, week in zip(lines, band.weeks, strict=True):
            _paint_tasks_index_week(plotter, line, week)
            for hit in tasks_index_link_hits(line):
                plotter.link(hit, week.dest)


def _paint_tasks_index_week(plotter: Plotter, row: Rect, week: TaskWeek) -> None:
    stub, dated, write = tasks_index_week_parts(row)
    _ink_text(
        plotter,
        stub,
        f"W{week.iso_week:02d}",
        TypeRef(step="chrome", emphasis="strong"),
        gray=INK,
        align="left",
    )
    _ink_text(
        plotter,
        dated,
        short_date_range(week.monday, week.sunday),
        TypeRef(step="label"),
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    rule_y = tasks_index_rule_y(row)
    plotter.line(
        write.x,
        rule_y,
        write.right,
        rule_y,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )


def task_row_count(well: Rect, floor: int = 1) -> int:
    """Tick rows that fill ≈⅔ of the well (minus ``TASK_GAP``), unlabeled."""
    target = (well.h - TASK_GAP) * TASK_CHECKLIST_FRAC
    usable = target - FOCUS_PAD_TOP - FOCUS_PAD_BOT
    if usable < TICK:
        fitted = 1
    else:
        fitted = max(1, int((usable - TICK) / FOCUS_PITCH) + 1)
    return max(floor, fitted)


def task_seats(well: Rect, rows_n: int | None = None) -> tuple[Rect, Rect]:
    """Unlabeled checklist ≈⅔ of well (minus ``TASK_GAP``); Notes take the leftover."""
    n = task_row_count(well) if rows_n is None else rows_n
    check, rest = well.split_top(checklist_content_height(n, labeled=False))
    notes = Rect(rest.x, rest.y + TASK_GAP, rest.w, rest.h - TASK_GAP)
    return check, notes


def paint_task(
    plotter: Plotter, box: Rect, page: TasksWeekPage, *, ramp: TypeRamp | None = None
) -> None:
    """Weekly Tasks dest — unlabeled ⅔ checklist + leftover notes. Chip is the week."""
    ramp = _bound_ramp(plotter, ramp)
    rows_n = task_row_count(box, floor=page.rows)
    checklist, notes = task_seats(box, rows_n)
    _paint_checklist_box(plotter, checklist, rows=rows_n, ramp=ramp)
    _paint_note_box(plotter, notes, label="Notes", ramp=ramp)


REVIEW_INDEX_BAND_GAP = 1.6
REVIEW_INDEX_MONTH_W = 20.0
REVIEW_INDEX_LABEL_GAP = 1.6
REVIEW_INDEX_CHIP_GAP = 1.2
REVIEW_INDEX_CHIP_INSET_X = 0.35
REVIEW_INDEX_CHIP_H = 6.8
REVIEW_GAP = 2.6
REVIEW_DAY_GAP = 1.0
REVIEW_STRIP_H = 18.0
REVIEW_DAY_INSET_X = 0.7
REVIEW_DAY_INSET_Y = 0.55
REVIEW_DOW_H = 3.6
REVIEW_NUM_H = 5.4


def review_index_cols(week_counts: tuple[int, ...]) -> int:
    """Shared chip-column count so month rows align across the grid."""
    return max((max(1, count) for count in week_counts), default=1)


def review_index_month_rows(well: Rect, n: int) -> tuple[Rect, ...]:
    """Equal-height month rows. Hairlines read across; weeks are the chips."""
    return rows(well, n, gap=REVIEW_INDEX_BAND_GAP)


def review_index_row_parts(
    row: Rect, n_weeks: int, n_cols: int
) -> tuple[Rect, tuple[Rect, ...]]:
    """Month stub | aligned week-chip columns — ``tracks.columns``."""
    stub_w = REVIEW_INDEX_MONTH_W
    grid_w = max(row.w - stub_w - REVIEW_INDEX_LABEL_GAP, 1)
    stub, grid = columns(row, 2, gap=REVIEW_INDEX_LABEL_GAP, weights=(stub_w, grid_w))
    cells = columns(grid, n_cols, gap=REVIEW_INDEX_CHIP_GAP)
    return stub, cells[:n_weeks]


def review_index_chip(cell: Rect) -> Rect:
    """Content-height chip, vertically centered — dense cell, not a stretched box."""
    h = min(REVIEW_INDEX_CHIP_H, cell.h)
    return Rect(
        cell.x + REVIEW_INDEX_CHIP_INSET_X,
        cell.y + (cell.h - h) / 2,
        max(cell.w - 2 * REVIEW_INDEX_CHIP_INSET_X, 1),
        h,
    )


def review_index_link_hits(cell: Rect) -> tuple[Rect, ...]:
    """Whole chip is the dest hit — no write-in on the dense grid."""
    return (review_index_chip(cell),)


def review_index_rule_y(row: Rect) -> float:
    """Month hairline — row floor, spanning the well so months read across."""
    return row.bottom


def paint_review_index(
    plotter: Plotter, box: Rect, index: ReviewIndex, *, ramp: TypeRamp | None = None
) -> None:
    """``ReviewIndex`` — dense week chips in several columns; month headers + hairlines."""
    _bound_ramp(plotter, ramp)
    counts = tuple(len(band.weeks) for band in index.bands)
    n_cols = review_index_cols(counts)
    bands = review_index_month_rows(box, len(index.bands))
    for i, (row, band) in enumerate(zip(bands, index.bands, strict=True)):
        stub, cells = review_index_row_parts(row, len(band.weeks), n_cols)
        _ink_text(
            plotter,
            stub,
            band.name,
            TypeRef(step="label", emphasis="strong"),
            gray=INK,
            small_caps=True,
            align="left",
        )
        for cell, week in zip(cells, band.weeks, strict=True):
            _paint_review_index_chip(plotter, cell, week)
            for hit in review_index_link_hits(cell):
                plotter.link(hit, week.dest)
        if i + 1 < len(bands):
            rule_y = review_index_rule_y(row)
            plotter.line(
                box.x,
                rule_y,
                box.right,
                rule_y,
                stroke_width=HAIR,
                stroke_gray=SOFT,
            )


def _paint_review_index_chip(plotter: Plotter, cell: Rect, week: ReviewWeek) -> None:
    chip = review_index_chip(cell)
    plotter.rect(chip, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    _ink_text(
        plotter,
        chip,
        f"W{week.iso_week:02d}",
        TypeRef(step="chrome", emphasis="strong"),
        gray=INK,
        align="center",
    )


def review_seats(well: Rect) -> tuple[Rect, Rect]:
    """Mon–Sun cue strip over leftover week narrative. Strip is content-height; notes flex."""
    strip, rest = well.split_top(REVIEW_STRIP_H)
    notes = Rect(rest.x, rest.y + REVIEW_GAP, rest.w, rest.h - REVIEW_GAP)
    return strip, notes


def review_day_cues(strip: Rect) -> tuple[Rect, ...]:
    """Seven equal day columns — ``tracks.columns``. Horizon scan, not status slices."""
    return columns(strip, 7, gap=REVIEW_DAY_GAP)


def review_day_parts(cue: Rect) -> tuple[Rect, Rect]:
    """Dow+date label | one-line write-in. ``tracks`` after a quiet inset."""
    inner = cue.inset(REVIEW_DAY_INSET_X, REVIEW_DAY_INSET_Y)
    label_h = REVIEW_DOW_H + REVIEW_NUM_H
    return inner.split_top(label_h)


def review_day_link_hits(cue: Rect) -> tuple[Rect, ...]:
    """Label only. Write-in stays unlinkable (same as ``paint_meetings_index`` / ``paint_tasks_index``)."""
    label, _write = review_day_parts(cue)
    return (label,)


def review_day_rule_y(cue: Rect) -> float:
    """One-line prompt baseline — mid write pocket, not the hairline box floor."""
    _label, write = review_day_parts(cue)
    return write.y + min(4.15, write.h * 0.55)


def paint_review(
    plotter: Plotter, box: Rect, page: ReviewWeekPage, *, ramp: TypeRamp | None = None
) -> None:
    """``ReviewWeekPage`` — seven day cues, then unlabeled week narrative. Chrome names the page."""
    ramp = _bound_ramp(plotter, ramp)
    strip, notes = review_seats(box)
    for cue, day in zip(review_day_cues(strip), page.days, strict=True):
        _paint_review_day_cue(plotter, cue, day)
        if day.dest:
            for hit in review_day_link_hits(cue):
                plotter.link(hit, day.dest)
    _paint_note_box(plotter, notes, ramp=ramp)


def _paint_review_day_cue(plotter: Plotter, cue: Rect, day: ReviewDay) -> None:
    """Mini write: weekday + date over a one-line prompt. Hairline pocket."""
    plotter.rect(cue, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    label, write = review_day_parts(cue)
    ink = INK if day.dest else MUTED
    dow = Rect(label.x, label.y, label.w, REVIEW_DOW_H)
    num = Rect(label.x, dow.bottom, label.w, REVIEW_NUM_H)
    _ink_text(
        plotter,
        dow,
        day.weekday_label,
        TypeRef(step="caption"),
        gray=MUTED,
        small_caps=True,
        align="center",
    )
    _ink_text(
        plotter,
        num,
        str(day.day.day),
        TypeRef(step="eyebrow", emphasis="strong"),
        gray=ink,
        align="center",
    )
    rule_y = review_day_rule_y(cue)
    plotter.line(
        write.x,
        rule_y,
        write.right,
        rule_y,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )


def paint_quarter(
    plotter: Plotter, box: Rect, grid: QuarterGrid, *, ramp: TypeRamp | None = None
) -> None:
    """Year-density minis, content-height Focus over flex Notes."""
    ramp = _bound_ramp(plotter, ramp)
    months, focus, notes = quarter_seats(box)
    for cell, month in zip(months, grid.months, strict=True):
        _paint_mini_month(plotter, cell, month, ramp=ramp)
    _paint_focus_box(plotter, focus, ramp=ramp)
    _paint_note_box(plotter, notes, label="Notes", ramp=ramp)


def quarter_seats(
    box: Rect,
) -> tuple[tuple[Rect, Rect, Rect], Rect, Rect]:
    """Short year-density month band; leftover is Focus over flex Notes."""
    cal_h = rows(box, 4, gap=2.6)[0].h
    cal_band, rest = box.split_top(cal_h)
    leftover = Rect(rest.x, rest.y + 2.6, rest.w, rest.h - 2.6)
    focus, notes = _stack_focus_notes(leftover)
    return columns(cal_band, 3, gap=4.0), focus, notes


def _stack_focus_notes(stack: Rect) -> tuple[Rect, Rect]:
    """Focus shrinks to checklist content; Notes takes the leftover."""
    gap = 2.6
    focus, rest = stack.split_top(focus_content_height())
    notes = Rect(rest.x, rest.y + gap, rest.w, rest.h - gap)
    return focus, notes


def _paint_note_box(
    plotter: Plotter,
    box: Rect,
    *,
    label: str | None = None,
    ramp: TypeRamp | None = None,
) -> None:
    """Lined writing box — outline + daily-notes rhythm. Not a Notes section."""
    if ramp is not None:
        plotter.ramp = ramp
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    top = 1.2
    if label:
        header_h = 3.4
        _ink_text(
            plotter,
            Rect(box.x + 1.3, box.y + 0.7, box.w - 2.6, header_h),
            label,
            TypeRef(step="label"),
            gray=MUTED,
            small_caps=True,
            align="left",
        )
        top = header_h + 1.4
    inset = Rect(box.x + 1.1, box.y + top, box.w - 2.2, box.h - top - 1.2)
    pitch = 4.15
    y = inset.y + pitch
    while y < inset.bottom - 0.15:
        plotter.line(inset.x, y, inset.right, y, stroke_width=RULE, stroke_gray=RULE_C)
        y += pitch


FOCUS_ROWS = 7
TICK = 2.4
FOCUS_PITCH = 4.8
FOCUS_LABEL_H = 3.4
FOCUS_PAD_TOP = 0.8
FOCUS_PAD_MID = 1.2
FOCUS_PAD_BOT = 1.4


def checklist_content_height(rows: int, *, labeled: bool = True) -> float:
    """Tight checklist rows + pad — label band optional. Not a fraction of the parent."""
    rows_h = TICK + (max(1, rows) - 1) * FOCUS_PITCH
    pads = FOCUS_PAD_TOP + FOCUS_PAD_BOT
    if labeled:
        pads += FOCUS_LABEL_H + FOCUS_PAD_MID
    return pads + rows_h


def focus_content_height() -> float:
    return checklist_content_height(FOCUS_ROWS)


def _paint_focus_box(
    plotter: Plotter, box: Rect, *, ramp: TypeRamp | None = None
) -> None:
    """Outlined FOCUS checklist — empty ticks + underline. Not a section."""
    _paint_checklist_box(plotter, box, label="Focus", rows=FOCUS_ROWS, ramp=ramp)


def paint_priorities(
    plotter: Plotter, box: Rect, priorities: Priorities, *, ramp: TypeRamp | None = None
) -> None:
    _paint_checklist_box(
        plotter, box, label=priorities.label, rows=priorities.rows, ramp=ramp
    )


def _paint_checklist_box(
    plotter: Plotter,
    box: Rect,
    *,
    rows: int,
    label: str | None = None,
    ramp: TypeRamp | None = None,
) -> None:
    if ramp is not None:
        plotter.ramp = ramp
    plotter.rect(box, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT)
    y = box.y + FOCUS_PAD_TOP
    if label:
        tag = Rect(box.x + 1.3, box.y + FOCUS_PAD_TOP, box.w - 2.6, FOCUS_LABEL_H)
        _ink_text(
            plotter,
            tag,
            label,
            TypeRef(step="label"),
            gray=MUTED,
            small_caps=True,
            align="left",
        )
        y = box.y + FOCUS_PAD_TOP + FOCUS_LABEL_H + FOCUS_PAD_MID
    x = box.x + 1.6
    right = box.right - 1.6
    for _ in range(max(1, rows)):
        _paint_focus_row(plotter, x, y, right)
        y += FOCUS_PITCH


def _paint_focus_row(plotter: Plotter, x: float, y: float, right: float) -> None:
    tick = Rect(x, y, TICK, TICK)
    plotter.rect(tick, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=INK)
    plotter.line(
        tick.right + 1.4,
        tick.bottom,
        right,
        tick.bottom,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )


def _paint_mini_month(
    plotter: Plotter, box: Rect, month: AnnualMonth, *, ramp: TypeRamp | None = None
) -> None:
    if ramp is not None:
        plotter.ramp = ramp
    pressed = month.dest is not None
    title_h = 3.5
    dow_h = 2.5
    title = Rect(box.x, box.y, box.w, title_h)
    _ink_text(
        plotter,
        title,
        month.name[:3],
        TypeRef(step="label", emphasis="strong" if pressed else "regular"),
        gray=INK if pressed else MUTED,
        small_caps=True,
        align="left",
    )
    if month.dest:
        plotter.link(title, month.dest)
    dow = Rect(box.x, box.y + title_h, box.w, dow_h)
    tracks = columns(box, 7)
    for i, label in enumerate(month.weekday_labels):
        col = tracks[i]
        cell = Rect(col.x, dow.y, col.w, dow.h)
        _ink_text(
            plotter,
            cell,
            label[0],
            TypeRef(step="micro"),
            gray=GHOST,
            small_caps=True,
            align="center",
        )
    rule_y = dow.bottom
    plotter.line(box.x, rule_y, box.right, rule_y, stroke_width=HAIR, stroke_gray=SOFT)
    body = Rect(box.x, rule_y + 0.25, box.w, box.h - title_h - dow_h - 0.25)
    for band, week in zip(rows(body, 6), month.weeks, strict=False):
        for c, cell in enumerate(week):
            if cell.day is None:
                continue
            col = tracks[c]
            num = Rect(col.x, band.y, col.w, band.h)
            here = (
                month.highlight_day is not None
                and cell.in_month
                and cell.day == month.highlight_day
            )
            if here:
                mark = num.inset(0.12, 0.18)
                plotter.rect(mark, stroke=False, fill=True, fill_gray=INK)
                _ink_text(
                    plotter,
                    num,
                    str(cell.day),
                    TypeRef(step="caption", emphasis="strong"),
                    gray=PAPER,
                    align="center",
                )
                continue
            linked = cell.dest is not None
            ink = MUTED if not cell.in_month else (INK if linked else MUTED)
            _ink_text(
                plotter,
                num,
                str(cell.day),
                TypeRef(
                    step="caption",
                    emphasis="strong" if linked and cell.in_month else "regular",
                ),
                gray=ink,
                align="center",
            )
            if linked:
                plotter.link(num, cell.dest)


HABIT_DAY_W = 13.0
HABIT_DOW_W = 5.2
HABIT_NAME_H = 16.0
HABIT_BODY_GAP = 0.5
HABIT_WASH = 247 / 255
HABIT_WASH_CROSS = 238 / 255


def habit_dow_letter(year: int, month: int, day: int) -> str:
    """Monday-start calendar letter: M T W T F S S."""
    return WEEKDAY_LABELS[date(year, month, day).weekday()][0]


def habit_seats(
    box: Rect, days: int, habits: int
) -> tuple[Rect, tuple[Rect, ...], tuple[Rect, ...]]:
    """Day labels left, habit name slots across the top. ``habits`` comes from the spec."""
    day_col, rest = box.split_left(HABIT_DAY_W)
    name_band, below = rest.split_top(HABIT_NAME_H)
    body = Rect(below.x, below.y + HABIT_BODY_GAP, below.w, below.h - HABIT_BODY_GAP)
    names = columns(name_band, habits, gap=0.4)
    bands = rows(body, max(1, days), gap=0.15)
    return day_col, names, bands


def _wash(plotter: Plotter, box: Rect, gray: float) -> None:
    plotter.rect(box, stroke=False, fill=True, fill_gray=gray)


def _stripe_span(
    tracks: tuple[Rect, ...], index: int, *, axis: str, end: float
) -> tuple[float, float]:
    """Continuous zebra span covering a track plus half the neighboring gaps."""
    track = tracks[index]
    if axis == "y":
        start = (tracks[index - 1].bottom + track.y) / 2 if index else track.y
        stop = (
            (track.bottom + tracks[index + 1].y) / 2 if index + 1 < len(tracks) else end
        )
        return start, stop
    start = (tracks[index - 1].right + track.x) / 2 if index else track.x
    stop = (track.right + tracks[index + 1].x) / 2 if index + 1 < len(tracks) else end
    return start, stop


def paint_habit_grid(
    plotter: Plotter, box: Rect, grid: HabitGrid, *, ramp: TypeRamp | None = None
) -> None:
    """Days down the left (``1 W``), habit name slots across the top, pale zebra."""
    _bound_ramp(plotter, ramp)
    habits = max(1, grid.rows)
    day_col, names, bands = habit_seats(box, grid.days, habits)
    matrix = Rect(
        names[0].x, bands[0].y, names[-1].right - names[0].x, box.bottom - bands[0].y
    )
    day_tracks = columns(matrix, habits, gap=0.4)
    for i, _band in enumerate(bands):
        if i % 2 == 0:
            continue
        y0, y1 = _stripe_span(bands, i, axis="y", end=box.bottom)
        _wash(plotter, Rect(day_col.x, y0, box.right - day_col.x, y1 - y0), HABIT_WASH)
    for j, _col in enumerate(day_tracks):
        if j % 2 == 0:
            continue
        x0, x1 = _stripe_span(day_tracks, j, axis="x", end=day_tracks[-1].right)
        _wash(
            plotter, Rect(x0, names[0].y, x1 - x0, box.bottom - names[0].y), HABIT_WASH
        )
    for i, band in enumerate(bands):
        if i % 2 == 0:
            continue
        for j, col in enumerate(day_tracks):
            if j % 2 == 0:
                continue
            _wash(plotter, Rect(col.x, band.y, col.w, band.h), HABIT_WASH_CROSS)
    for col in names:
        plotter.line(
            col.x + 0.3,
            col.bottom - 1.1,
            col.right - 0.3,
            col.bottom - 1.1,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )
    plotter.line(
        box.x,
        names[0].bottom,
        box.right,
        names[0].bottom,
        stroke_width=HAIR,
        stroke_gray=SOFT,
    )
    letter_w = HABIT_DOW_W
    num_w = day_col.w - letter_w
    for i, band in enumerate(bands):
        day_n = i + 1
        _ink_text(
            plotter,
            Rect(day_col.x, band.y, num_w - 0.6, band.h),
            str(day_n),
            TypeRef(step="micro"),
            gray=MUTED,
            align="right",
        )
        _ink_text(
            plotter,
            Rect(day_col.x + num_w, band.y, letter_w - 0.3, band.h),
            habit_dow_letter(grid.year, grid.month, day_n),
            TypeRef(step="micro"),
            gray=MUTED,
            align="left",
        )
        if i < len(grid.day_dests) and grid.day_dests[i]:
            plotter.link(Rect(day_col.x, band.y, day_col.w, band.h), grid.day_dests[i])
        for col in day_tracks:
            cell = Rect(col.x, band.y, col.w, band.h).inset(0.2, 0.12)
            plotter.rect(
                cell, stroke=True, fill=False, stroke_width=HAIR, stroke_gray=SOFT
            )


def paint_month_grid(
    plotter: Plotter, box: Rect, grid: MonthGrid, *, ramp: TypeRamp | None = None
) -> None:
    ramp = _bound_ramp(plotter, ramp)
    gutter = 8.0
    day_grid = Rect(box.x + gutter, box.y, box.w - gutter, box.h)
    tracks = columns(day_grid, 7)
    dow_h = 4.2
    header = Rect(day_grid.x, box.y, day_grid.w, dow_h)
    # Shared inset + left align for weekday letters and day numerals.
    inset = 0.5
    weekday = TypeRef(step="label")
    for i, label in enumerate(grid.weekday_labels):
        col = tracks[i]
        _ink_text(
            plotter,
            Rect(col.x + inset, header.y, col.w - 2 * inset, header.h),
            label[0],
            weekday,
            gray=MUTED,
            small_caps=True,
            align="left",
        )
    plotter.line(
        box.x,
        header.bottom,
        box.right,
        header.bottom,
        stroke_width=HAIR,
        stroke_gray=INK,
    )

    body = Rect(box.x, header.bottom + 0.6, box.w, box.bottom - header.bottom - 0.6)
    bands = rows(body, max(1, len(grid.weeks)))
    week_num = TypeRef(step="caption")
    day_num = TypeRef(step="body", emphasis="strong")
    for r, (band, week) in enumerate(zip(bands, grid.weeks, strict=False)):
        monday = _week_monday(grid, week, r)
        if monday is not None:
            iso = monday.isocalendar().week
            _ink_text(
                plotter,
                Rect(box.x, band.y, gutter - 0.4, band.h),
                f"W{iso:02d}",
                week_num,
                gray=MUTED,
                small_caps=True,
                align="left",
            )
            if r < len(grid.week_dests) and grid.week_dests[r]:
                plotter.link(Rect(box.x, band.y, gutter, band.h), grid.week_dests[r])
        for c, day in enumerate(week):
            if day.day is None:
                continue
            col = tracks[c]
            cell = Rect(col.x, band.y, col.w, band.h)
            _ink_text(
                plotter,
                Rect(cell.x + inset, cell.y + 0.7, cell.w - 2 * inset, 5.4),
                str(day.day),
                day_num,
                gray=INK,
                align="left",
            )
            if day.dest:
                plotter.link(cell, day.dest)
        plotter.line(
            box.x,
            band.bottom,
            box.right,
            band.bottom,
            stroke_width=HAIR,
            stroke_gray=SOFT,
        )


def _week_monday(grid: MonthGrid, week: tuple, _row: int) -> date | None:
    for c, cell in enumerate(week):
        if cell.day is None:
            continue
        day = date(grid.year, grid.month, cell.day)
        return day - timedelta(days=c)
    return None


def paint_week(
    plotter: Plotter, box: Rect, week: WeekStrip, *, ramp: TypeRamp | None = None
) -> None:
    ramp = _bound_ramp(plotter, ramp)
    weekday = TypeRef(step="label")
    day_num = TypeRef(step="title", emphasis="strong")
    for band, day in zip(rows(box, max(1, len(week.days))), week.days, strict=False):
        ink = INK if day.in_month else MUTED
        _ink_text(
            plotter,
            Rect(band.x, band.y + 0.45, 14.0, 5.0),
            day.weekday_label,
            weekday,
            gray=MUTED,
            small_caps=True,
            align="left",
        )
        _ink_text(
            plotter,
            Rect(band.x + 14.0, band.y + 0.1, 12.0, 5.8),
            str(day.day.day),
            day_num,
            gray=ink,
            align="left",
        )
        if not day.in_month or day.day.day == 1:
            _ink_text(
                plotter,
                Rect(band.x + 26.0, band.y + 0.55, 22.0, 4.8),
                MONTH_NAMES[day.day.month - 1][:3],
                weekday,
                gray=MUTED,
                small_caps=True,
                align="left",
            )
        if day.dest:
            plotter.link(Rect(band.x, band.y, band.w, 6.4), day.dest)
        rule_y = band.y + 6.9
        pitch = 4.15
        while rule_y < band.bottom - 1.15:
            plotter.line(
                band.x,
                rule_y,
                band.right,
                rule_y,
                stroke_width=RULE,
                stroke_gray=RULE_C,
            )
            rule_y += pitch
        plotter.line(
            band.x,
            band.bottom,
            band.right,
            band.bottom,
            stroke_width=HAIR,
            stroke_gray=SOFT,
        )


def paint_schedule(
    plotter: Plotter, box: Rect, schedule: Schedule, *, ramp: TypeRamp | None = None
) -> None:
    if ramp is not None:
        plotter.ramp = ramp
    header_h = 3.4
    tag = Rect(box.x, box.y, box.w, header_h)
    _ink_text(
        plotter,
        tag,
        schedule.label,
        TypeRef(step="label"),
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    body = Rect(box.x, box.y + header_h + 0.4, box.w, box.h - header_h - 0.4)
    hours = schedule.hours or (8,)
    hour_ink = TypeRef(step="chrome")
    for band, hour in zip(rows(body, len(hours)), hours, strict=True):
        if shade_painted_hour(hour, schedule.work_hours):
            _wash(plotter, band, WASH)
        slot = Rect(band.x, band.y, 10.0, band.h)
        _ink_text(plotter, slot, f"{hour:2d}", hour_ink, gray=MUTED, align="left")
        plotter.line(
            band.x,
            band.bottom,
            band.right,
            band.bottom,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )


def paint_notes(
    plotter: Plotter, box: Rect, notes: Notes, *, ramp: TypeRamp | None = None
) -> None:
    if ramp is not None:
        plotter.ramp = ramp
    header_h = 3.4
    tag = Rect(box.x, box.y, box.w, header_h)
    _ink_text(
        plotter,
        tag,
        notes.label,
        TypeRef(step="label"),
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    body = Rect(box.x, box.y + header_h + 0.4, box.w, box.h - header_h - 0.4)
    paint_lines(plotter, body)


def daily_left_seats(left: Rect) -> tuple[Rect, Rect]:
    """Schedule flex over a compact year-density mini-month."""
    return rows(
        left,
        2,
        gap=DAILY_MINI_GAP,
        weights=(left.h - DAILY_MINI_H - DAILY_MINI_GAP, DAILY_MINI_H),
    )


def daily_right_seats(right: Rect, priority_rows: int) -> tuple[Rect, Rect]:
    """Content-height Priorities over flex Notes. No dead band under the last tick."""
    prio_h = checklist_content_height(priority_rows)
    return rows(
        right,
        2,
        gap=DAILY_PRIO_GAP,
        weights=(prio_h, max(right.h - prio_h - DAILY_PRIO_GAP, 1)),
    )


# Sealed BuJo paper — painter constants until a second pattern exists.
BUJO_GUTTER_MM = 8.0
BUJO_ROW_MM = 5.0
BUJO_DOT = 0.32
BUJO_DOT_PITCH = 5.0
BUJO_MIGRATE_LABEL_H = 3.4
_BUJO_SYMBOL_W = 10.0
_BUJO_MEANING_GAP = 2.0
# Fraction of body em — under Jost Book stem (~0.085em) so the bar is lighter than glyphs.
_BUJO_STRIKE_EM = 0.045
# Genesis • only — same glyph size; PAPER ring via offset copies (not a scaled fill).
# Draw order punches white only where the ring crosses INK x/>/<; no blend mode.
# ~0.29 mm at title-strong 11 pt ≈ 3.4 px on Nomad 300 ppi.
_BUJO_HALO_EM = 0.075
_BUJO_HALO_RAYS = 12


def _bujo_strike_width(ramp: TypeRamp) -> float:
    """Body-relative cancel bar, lighter than inked glyph stems."""
    return pt_mm(float(ramp.ink("body").size)) * _BUJO_STRIKE_EM


def _bujo_halo_offset(size_pt: float) -> float:
    """Title-strong-relative ring width; the • cut itself stays unscaled."""
    return pt_mm(float(size_pt)) * _BUJO_HALO_EM


def _paint_bujo_dots(plotter: Plotter, box: Rect) -> None:
    """5 mm dotted well — RULE_C dots on a sealed pitch."""
    nx = max(2, int(box.w / BUJO_DOT_PITCH))
    ny = max(2, int(box.h / BUJO_DOT_PITCH))
    inset = Rect(box.x, box.y, nx * BUJO_DOT_PITCH, ny * BUJO_DOT_PITCH)
    for band in rows(inset, ny):
        for cell in columns(band, nx):
            plotter.rect(
                Rect(
                    cell.x + (cell.w - BUJO_DOT) / 2,
                    cell.y + (cell.h - BUJO_DOT) / 2,
                    BUJO_DOT,
                    BUJO_DOT,
                ),
                stroke=False,
                fill=True,
                fill_gray=RULE_C,
            )


def _bujo_key_face(plotter: Plotter) -> tuple[str, float, TypeRef]:
    """Title-strong cut the Key marks paint with."""
    ink = plotter.ramp.ink("title", "strong")
    path = str(plotter.ramp.catalog.path(ink.family, ink.weight))
    return path, float(ink.size), TypeRef(step="title", emphasis="strong")


def _bujo_key_mark_box(band: Rect) -> Rect:
    return Rect(band.x, band.y, _BUJO_SYMBOL_W, band.h)


def _bujo_key_seat(mark_box: Rect) -> tuple[float, float]:
    """Shared compose seat: mark-cell center. Glyph ink nests land here."""
    return mark_box.x + mark_box.w * 0.5, mark_box.y + mark_box.h * 0.5


def _paint_bujo_key_glyph(
    plotter: Plotter,
    char: str,
    path: str,
    size: float,
    mark: TypeInk | TypeRef,
    seat: tuple[float, float],
    *,
    gray: float = INK,
) -> None:
    """Place one Key glyph by its vendored-face ink nest, not box-centered text."""
    ink = glyph_ink(path, char, size)
    _ink_text(
        plotter,
        ink_rect(seat, ink),
        char,
        mark,
        gray=gray,
        align="left",
        origin=origin_for_nest(seat, ink),
    )


def _paint_bujo_key_haloed_period(
    plotter: Plotter,
    path: str,
    size: float,
    ref: TypeRef,
    seat: tuple[float, float],
) -> None:
    """Genesis •: PAPER ring (offset copies), then the unscaled INK fill."""
    ring = _bujo_halo_offset(size)
    sx, sy = seat
    for i in range(_BUJO_HALO_RAYS):
        ang = 2.0 * math.pi * i / _BUJO_HALO_RAYS
        _paint_bujo_key_glyph(
            plotter,
            ".",
            path,
            size,
            ref,
            (sx + ring * math.cos(ang), sy + ring * math.sin(ang)),
            gray=PAPER,
        )
    _paint_bujo_key_glyph(plotter, ".", path, size, ref, seat)


def _paint_bujo_key_mark(
    plotter: Plotter,
    band: Rect,
    row: BujoKeySymbol,
    path: str,
    size: float,
    ref: TypeRef,
    seat: tuple[float, float],
) -> None:
    """Lone signifier, or shared • plus the task modifier on one ink seat."""
    if row.genesis:
        # Modifier first; haloed • on top so the knockout ring separates black-on-black.
        _paint_bujo_key_glyph(plotter, row.mark, path, size, ref, seat)
        _paint_bujo_key_haloed_period(plotter, path, size, ref, seat)
        return
    if row.mark == ".":
        _paint_bujo_key_glyph(plotter, ".", path, size, ref, seat)
        return
    _ink_text(
        plotter, _bujo_key_mark_box(band), row.mark, ref, gray=INK, align="center"
    )


def paint_bujo_key(
    plotter: Plotter, box: Rect, key: BujoKey, *, ramp: TypeRamp | None = None
) -> None:
    """Printed signifiers plus blank custom rows."""
    ramp = _bound_ramp(plotter, ramp)
    n = max(1, len(key.symbols) + max(0, key.custom_rows))
    symbol_w = _BUJO_SYMBOL_W
    path, size, ref = _bujo_key_face(plotter)
    for i, band in enumerate(rows(box, n)):
        if i < len(key.symbols):
            row = key.symbols[i]
            mark_box = _bujo_key_mark_box(band)
            seat = _bujo_key_seat(mark_box)
            _paint_bujo_key_mark(plotter, band, row, path, size, ref, seat)
            meaning_x = band.x + symbol_w + _BUJO_MEANING_GAP
            meaning = Rect(
                meaning_x, band.y, band.w - symbol_w - _BUJO_MEANING_GAP, band.h
            )
            _ink_text(
                plotter,
                meaning,
                row.meaning,
                TypeRef(step="body"),
                gray=INK,
                align="left",
            )
            if row.strike:
                period = glyph_ink(path, ".", size)
                x1 = seat[0] - (period.cx - period.xmin)
                plotter.line(
                    x1,
                    seat[1],
                    meaning.right,
                    seat[1],
                    stroke_width=_bujo_strike_width(ramp),
                    stroke_gray=INK,
                )
        plotter.line(
            box.x,
            band.bottom,
            box.right,
            band.bottom,
            stroke_width=HAIR,
            stroke_gray=SOFT,
        )


def paint_bujo_index(
    plotter: Plotter, box: Rect, index: BujoIndex, *, ramp: TypeRamp | None = None
) -> None:
    """Index rows — label links; write-in stays unlinkable."""
    ramp = _bound_ramp(plotter, ramp)
    n = max(1, len(index.rows))
    label_w = min(42.0, box.w * 0.42)
    for band, row in zip(rows(box, n), index.rows, strict=False):
        label, write = band.split_left(label_w)
        if row.label:
            _ink_text(
                plotter,
                Rect(label.x, label.y, label.w - 1.2, label.h),
                row.label,
                TypeRef(step="body"),
                gray=INK,
                align="left",
            )
        if row.dest:
            plotter.link(label, row.dest)
        plotter.line(
            write.x,
            write.y + write.h * 0.72,
            write.right,
            write.y + write.h * 0.72,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )
        plotter.line(
            box.x,
            band.bottom,
            box.right,
            band.bottom,
            stroke_width=HAIR,
            stroke_gray=SOFT,
        )


def paint_future_log(
    plotter: Plotter, box: Rect, page: FutureLogPage, *, ramp: TypeRamp | None = None
) -> None:
    """Stacked month bands — name links to the monthly calendar list."""
    ramp = _bound_ramp(plotter, ramp)
    n = max(1, len(page.months))
    for band, month in zip(rows(box, n, gap=2.6), page.months, strict=True):
        head, body = band.split_top(5.2)
        _ink_text(
            plotter,
            head,
            month.name,
            TypeRef(step="title", emphasis="strong"),
            gray=INK,
            align="left",
        )
        plotter.link(head, month.dest)
        y = body.y + 4.15
        while y < body.bottom - 0.15:
            plotter.line(
                body.x, y, body.right, y, stroke_width=RULE, stroke_gray=RULE_C
            )
            y += 4.15
        plotter.line(
            box.x,
            band.bottom,
            box.right,
            band.bottom,
            stroke_width=HAIR,
            stroke_gray=SOFT,
        )


def paint_monthly_calendar_list(
    plotter: Plotter,
    box: Rect,
    cal: MonthlyCalendarList,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Day list — numeral + weekday; each row links to that rapid-log dest."""
    ramp = _bound_ramp(plotter, ramp)
    n = max(1, len(cal.days))
    num_w = 10.0
    for band, day in zip(rows(box, n), cal.days, strict=True):
        _ink_text(
            plotter,
            Rect(band.x, band.y, num_w, band.h),
            str(day.day),
            TypeRef(step="body", emphasis="strong"),
            gray=INK,
            align="right",
        )
        _ink_text(
            plotter,
            Rect(band.x + num_w + 2.0, band.y, 16.0, band.h),
            day.weekday,
            TypeRef(step="label"),
            gray=MUTED,
            small_caps=True,
            align="left",
        )
        plotter.link(band, day.dest)
        plotter.line(
            box.x,
            band.bottom,
            box.right,
            band.bottom,
            stroke_width=HAIR,
            stroke_gray=SOFT,
        )


def paint_monthly_task_well(
    plotter: Plotter,
    box: Rect,
    well: MonthlyTaskWell,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Migrate lines over a lined task well."""
    ramp = _bound_ramp(plotter, ramp)
    migrate_h = BUJO_MIGRATE_LABEL_H + well.migrate_lines * BUJO_ROW_MM + 2.4
    migrate, rest = box.split_top(min(migrate_h, box.h * 0.4))
    _ink_text(
        plotter,
        Rect(migrate.x, migrate.y, migrate.w, BUJO_MIGRATE_LABEL_H),
        "Migrate",
        TypeRef(step="label"),
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    y = migrate.y + BUJO_MIGRATE_LABEL_H + BUJO_ROW_MM
    stop = migrate.bottom - 0.4
    for _ in range(well.migrate_lines):
        if y > stop:
            break
        plotter.line(
            migrate.x, y, migrate.right, y, stroke_width=RULE, stroke_gray=RULE_C
        )
        y += BUJO_ROW_MM
    tasks = Rect(rest.x, rest.y + 2.2, rest.w, max(rest.h - 2.2, 1))
    _paint_note_box(plotter, tasks, label="Tasks", ramp=ramp)


def paint_rapid_log(
    plotter: Plotter, box: Rect, _page: RapidLogPage, *, ramp: TypeRamp | None = None
) -> None:
    """8 mm signifier gutter + 5 mm dotted well. Sealed paper, not a Spec knob."""
    ramp = _bound_ramp(plotter, ramp)
    gutter, well = box.split_left(BUJO_GUTTER_MM)
    plotter.line(
        gutter.right,
        box.y,
        gutter.right,
        box.bottom,
        stroke_width=HAIR,
        stroke_gray=SOFT,
    )
    y = gutter.y + BUJO_ROW_MM
    while y < gutter.bottom - 0.2:
        plotter.line(gutter.x, y, gutter.right, y, stroke_width=HAIR, stroke_gray=SOFT)
        y += BUJO_ROW_MM
    _paint_bujo_dots(plotter, well)


def paint_collection(
    plotter: Plotter,
    box: Rect,
    _leaf: CollectionLeaf,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Full-well 5 mm dots — same sealed pattern as the rapid-log well."""
    _bound_ramp(plotter, ramp)
    _paint_bujo_dots(plotter, box)


def paint_daily(
    plotter: Plotter,
    box: Rect,
    schedule: Schedule,
    mini: AnnualMonth,
    priorities: Priorities,
    notes: Notes,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Daily well — schedule + mini-month | priorities + notes. Allowlisted."""
    ramp = _bound_ramp(plotter, ramp)
    left, right = columns(box, 2, gap=COL_GAP, weights=DAILY_COL_WEIGHTS)
    sched_box, mini_box = daily_left_seats(left)
    prio_box, notes_box = daily_right_seats(right, priorities.rows)
    paint_schedule(plotter, sched_box, schedule, ramp=ramp)
    _paint_mini_month(plotter, mini_box, mini, ramp=ramp)
    paint_priorities(plotter, prio_box, priorities, ramp=ramp)
    paint_notes(plotter, notes_box, notes, ramp=ramp)


def well_rect(device: Device) -> Rect:
    """Writable well between header and bottom nav, inset by writing clearance."""
    top = device.content_top + HEADER_H + 2.2
    bottom = device.page_height - device.bottom_clearance - NAV_H - 2.2
    m = device.writing_clearance
    return Rect(m, top, device.page_width - 2 * m, bottom - top)


def strip_items(page: Page) -> tuple[tuple[str, str], ...]:
    dests: dict[str, str] = {}
    for item in page.nav:
        if item.dest.startswith("year-"):
            dests["Year"] = item.dest
        elif item.dest.startswith("quarter-"):
            dests["Quar"] = item.dest
        elif item.dest.endswith("-habits"):
            dests["Habit"] = item.dest
        elif item.dest.endswith("-tasks"):
            pass
        elif item.dest.startswith("month-"):
            dests["Mon"] = item.dest
        elif item.dest.startswith("bujo-key-"):
            dests["Key"] = item.dest
        elif item.dest.startswith("bujo-index-"):
            dests["Idx"] = item.dest
        elif item.dest.startswith("bujo-future-"):
            dests["Fut"] = item.dest
        elif item.dest.startswith("bujo-col-"):
            dests["Col"] = item.dest
        elif item.dest.startswith("projects-index-"):
            dests["Proj"] = item.dest
        elif item.dest.startswith("meetings-index-"):
            dests["Meet"] = item.dest
        elif item.dest.startswith("tasks-index-"):
            dests["Task"] = item.dest
        elif item.dest.startswith("review-index-"):
            dests["Rev"] = item.dest
        elif item.dest.startswith("week-"):
            dests["Week"] = item.dest
        elif "-notes-" in item.dest:
            dests["Notes"] = item.dest
        elif item.dest.startswith("favorites-"):
            dests["Fav"] = item.dest
        elif item.dest.startswith("my-100-"):
            dests["100"] = item.dest
        elif item.dest.startswith("checkoff-365-"):
            dests["365"] = item.dest
        elif item.dest.count("-") == 2 and item.dest[:4].isdigit():
            dests["Day"] = item.dest
    match page.lead:
        case AnnualGrid():
            dests["Year"] = page.dest
        case FavoritesPage():
            dests["Fav"] = page.dest
        case My100Page():
            pass
        case Checkoff365():
            dests["365"] = page.dest
        case QuarterGrid():
            dests["Quar"] = page.dest
        case MonthGrid():
            dests["Mon"] = page.dest
        case HabitGrid():
            dests["Habit"] = page.dest
        case ProjectsIndex():
            dests["Proj"] = page.dest
        case ProjectsBoard():
            pass
        case MeetingIndex():
            dests["Meet"] = page.dest
        case MeetingAgenda():
            pass
        case TasksIndex():
            dests["Task"] = page.dest
        case TasksWeekPage():
            pass
        case ReviewIndex():
            dests["Rev"] = page.dest
        case ReviewWeekPage():
            pass
        case WeekStrip():
            dests["Week"] = page.dest
        case Schedule():
            dests["Day"] = page.dest
        case Notes():
            dests["Notes"] = page.dest
            dests["Day"] = page.dest.rsplit("-notes-", 1)[0]
        case BujoKey():
            dests["Key"] = page.dest
        case BujoIndex():
            dests["Idx"] = page.dest
        case FutureLogPage():
            dests["Fut"] = page.dest
        case MonthlyCalendarList():
            dests["Mon"] = page.dest
        case MonthlyTaskWell():
            dests["Mon"] = dests.get("Mon", page.dest)
        case RapidLogPage():
            dests["Day"] = page.dest
        case CollectionLeaf():
            dests["Col"] = page.dest
        case (
            CoverTitle()
            | EngineeringPad()
            | StenoPad()
            | DotGridPad()
            | LinedPad()
            | PerspectivePad()
        ):
            pass
        case _ as unseen:
            assert_never(unseen)
    order = (
        "Key",
        "Idx",
        "Fut",
        "Year",
        "365",
        "Quar",
        "Mon",
        "Habit",
        "Week",
        "Rev",
        "Day",
        "Notes",
        "Fav",
        "100",
        "Col",
        "Proj",
        "Meet",
        "Task",
    )
    return tuple((label, dests[label]) for label in order if label in dests)


def strip_active(page: Page) -> str:
    match page.lead:
        case AnnualGrid():
            return "Year"
        case FavoritesPage():
            return "Fav"
        case My100Page():
            return "100"
        case Checkoff365():
            return "365"
        case QuarterGrid():
            return "Quar"
        case MonthGrid() | MonthlyCalendarList() | MonthlyTaskWell():
            return "Mon"
        case WeekStrip():
            return "Week"
        case Schedule() | RapidLogPage():
            return "Day"
        case Notes():
            return "Notes"
        case HabitGrid():
            return "Habit"
        case ProjectsIndex() | ProjectsBoard():
            return "Proj"
        case MeetingIndex() | MeetingAgenda():
            return "Meet"
        case TasksIndex() | TasksWeekPage():
            return "Task"
        case ReviewIndex() | ReviewWeekPage():
            return "Rev"
        case (
            CoverTitle()
            | EngineeringPad()
            | StenoPad()
            | DotGridPad()
            | LinedPad()
            | PerspectivePad()
        ):
            return ""
        case BujoKey():
            return "Key"
        case BujoIndex():
            return "Idx"
        case FutureLogPage():
            return "Fut"
        case CollectionLeaf():
            return "Col"
        case _ as unseen:
            assert_never(unseen)


ENG_HEADER_H = 14.0
ENG_HEADER_FIELDS = ("Subject", "Date", "Sheet")
# NOTES column dropped: its width goes to SUBJECT. DATE and SHEET stay compact twins.
ENG_HEADER_WEIGHTS = (0.50, 0.25, 0.25)
ENG_LABEL_INSET_X = 1.2
ENG_LABEL_INSET_Y = 1.0
ENG_LABEL_H = 4.2
ENG_MAJOR_EVERY = 5
ENG_PITCH_MM = 5.0  # hardcoded E2 mesh — not a Spec/TOML knob


@dataclass(frozen=True, slots=True)
class EngineeringGridMesh:
    """Centered square mesh: width-first pitch, majors on multiples of 5."""

    origin: Rect
    pitch: float
    nx: int
    ny: int


def engineering_front_seats(frame: Rect) -> tuple[Rect, Rect]:
    """One header row over the blank writing well. Same outer frame as the back grid."""
    return frame.split_top(ENG_HEADER_H)


def engineering_header_cells(header: Rect) -> tuple[Rect, ...]:
    """SUBJECT | DATE | SHEET — wide subject, two compact twins. No write-in rules."""
    return columns(header, len(ENG_HEADER_FIELDS), gap=0, weights=ENG_HEADER_WEIGHTS)


def engineering_grid_mesh(box: Rect) -> EngineeringGridMesh:
    """Width-first 5 mm clusters: fill the frame width, leftover height is the strip."""
    nx = max(
        ENG_MAJOR_EVERY,
        (int(box.w / ENG_PITCH_MM) // ENG_MAJOR_EVERY) * ENG_MAJOR_EVERY,
    )
    pitch = box.w / nx
    ny = max(
        ENG_MAJOR_EVERY,
        (int(box.h / pitch) // ENG_MAJOR_EVERY) * ENG_MAJOR_EVERY,
    )
    pitch = min(box.w / nx, box.h / ny)
    gw, gh = nx * pitch, ny * pitch
    ox = box.x + (box.w - gw) / 2
    oy = box.y + (box.h - gh) / 2
    return EngineeringGridMesh(Rect(ox, oy, gw, gh), pitch, nx, ny)


def paint_engineering_pad(
    plotter: Plotter,
    device: Device,
    pad: EngineeringPad,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Duplex computation pad — front three-cell header; back 5×5 grid. No holes."""
    ramp = _bound_ramp(plotter, ramp)
    frame = device.content_frame()
    match pad.face:
        case "front":
            _paint_engineering_frame(plotter, frame, stroke_gray=INK)
            header, _well = engineering_front_seats(frame)
            _paint_engineering_header(plotter, header, ramp=ramp)
        case "back":
            _paint_engineering_frame(plotter, frame, stroke_gray=MUTED)
            _paint_engineering_grid(plotter, frame)
        case _:
            raise ValueError(f"unknown engineering face {pad.face!r}")


def _paint_engineering_frame(
    plotter: Plotter, frame: Rect, *, stroke_gray: float
) -> None:
    """content_frame hairline — no hole-margin strip. Front INK, back MUTED."""
    plotter.rect(
        frame,
        stroke=True,
        fill=False,
        stroke_width=HAIR,
        stroke_gray=stroke_gray,
    )


def _paint_engineering_header(
    plotter: Plotter, header: Rect, *, ramp: TypeRamp
) -> None:
    plotter.ramp = ramp
    cells = engineering_header_cells(header)
    for i, (cell, label) in enumerate(zip(cells, ENG_HEADER_FIELDS, strict=True)):
        if i:
            plotter.line(
                cell.x,
                header.y,
                cell.x,
                header.bottom,
                stroke_width=RULE,
                stroke_gray=RULE_C,
            )
        _ink_text(
            plotter,
            Rect(
                cell.x + ENG_LABEL_INSET_X,
                cell.y + ENG_LABEL_INSET_Y,
                cell.w - 2 * ENG_LABEL_INSET_X,
                ENG_LABEL_H,
            ),
            label,
            TypeRef(step="caption"),
            gray=MUTED,
            small_caps=True,
            align="left",
        )
    plotter.line(
        header.x,
        header.bottom,
        header.right,
        header.bottom,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )


def _paint_engineering_grid(plotter: Plotter, box: Rect) -> None:
    """Square engineering mesh — minors RULE/RULE_C, majors every 5 HAIR/MUTED."""
    mesh = engineering_grid_mesh(box)
    grid = mesh.origin
    for i in range(mesh.nx + 1):
        x = grid.x + i * mesh.pitch
        major = i % ENG_MAJOR_EVERY == 0
        plotter.line(
            x,
            grid.y,
            x,
            grid.bottom,
            stroke_width=HAIR if major else RULE,
            stroke_gray=MUTED if major else RULE_C,
        )
    for j in range(mesh.ny + 1):
        y = grid.y + j * mesh.pitch
        major = j % ENG_MAJOR_EVERY == 0
        plotter.line(
            grid.x,
            y,
            grid.right,
            y,
            stroke_width=HAIR if major else RULE,
            stroke_gray=MUTED if major else RULE_C,
        )


STENO_PITCH_MM = 25.4 / 3  # hardcoded Gregg ⅓″ — not a Spec/TOML knob
# Ink on 20220804011810_steno.png (1404×1872 @ 300 ppi). No frame, no Spec knob.
# These are page-edge insets of that Nomad sheet. Seating turns them into
# offsets from Nomad's content frame, then applies the offsets to whatever
# device is being pressed.
_STENO_PNG_MM = 25.4 / 300
STENO_H_LEFT_MM = 42 * _STENO_PNG_MM
STENO_H_RIGHT_MM = 46 * _STENO_PNG_MM
STENO_H_TOP_MM = 127 * _STENO_PNG_MM
STENO_H_BOTTOM_MM = 91 * _STENO_PNG_MM
STENO_V_TOP_MM = 71 * _STENO_PNG_MM
STENO_V_BOTTOM_MM = 33 * _STENO_PNG_MM
STENO_DOT_W_MM = 4 * _STENO_PNG_MM
STENO_DOT_H_MM = 2 * _STENO_PNG_MM
STENO_DOT_PITCH_MM = 9.5 * _STENO_PNG_MM


@dataclass(frozen=True, slots=True)
class StenoRuling:
    """Top-aligned Gregg ruling: ⅓″ horizontals, one vertical center rule."""

    origin: Rect
    pitch: float
    n_lines: int
    center_x: float


def steno_ruling(box: Rect) -> StenoRuling:
    """Fit as many ⅓″ gaps as *box* allows. Center splits two equal columns."""
    n_gaps = max(1, int(box.h / STENO_PITCH_MM))
    used_h = n_gaps * STENO_PITCH_MM
    return StenoRuling(
        Rect(box.x, box.y, box.w, used_h),
        STENO_PITCH_MM,
        n_gaps + 1,
        box.x + box.w / 2,
    )


def _steno_frame_offsets() -> tuple[float, float, float, float]:
    """PNG page insets as offsets from Nomad's content frame.

    Positive is inside the frame. The measured sheet sits a hair outside
    the frame on the left, right, and bottom, so those three are negative.
    """
    anchor = NOMAD.content_frame()
    return (
        STENO_H_LEFT_MM - anchor.x,
        STENO_H_TOP_MM - anchor.y,
        STENO_H_RIGHT_MM - (NOMAD.page_width - anchor.right),
        STENO_H_BOTTOM_MM - (NOMAD.page_height - anchor.bottom),
    )


def steno_horizontal_field(device: Device) -> Rect:
    """Dotted field: PNG offsets applied to ``device.content_frame()``.

    Nomad reproduces the SuperNote sheet (Gregg ⅓″, 17 lines). Scribe
    keeps those same offsets from its own content frame, so the dots stay
    on the page and out of the bottom dead zone.
    """
    frame = device.content_frame()
    left, top, right, bottom = _steno_frame_offsets()
    return Rect(
        frame.x + left,
        frame.y + top,
        frame.w - left - right,
        frame.h - top - bottom,
    )


def _steno_center_ys(device: Device, field: Rect) -> tuple[float, float]:
    """Solid center, longer than *field* by the PNG's extra reach.

    Scribe's content frame starts at the page top, so the overhang above
    the frame is cut at y=0. The rule still starts above the first dots.
    """
    over_top = STENO_H_TOP_MM - STENO_V_TOP_MM
    over_bottom = STENO_H_BOTTOM_MM - STENO_V_BOTTOM_MM
    y0 = max(0.0, field.y - over_top)
    y1 = min(device.page_height, field.bottom + over_bottom)
    return y0, y1


def paint_steno_pad(
    plotter: Plotter,
    device: Device,
    pad: StenoPad,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Single-face Gregg pad — dotted ⅓″ lines, no frame. No header or holes."""
    _bound_ramp(plotter, ramp)
    _paint_steno_ruling(plotter, device)


def paint_dotgrid_page(
    plotter: Plotter,
    device: Device,
    pad: DotGridPad,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Single-face full-bleed clone-dot page. No header, holes, or chrome."""
    _bound_ramp(plotter, ramp)
    paint_dotgrid(plotter, device.page_rect())


def paint_lines(plotter: Plotter, box: Rect) -> None:
    """RULE_C horizontals at ``LINE_PITCH``. No pocket frame."""
    y = box.y + LINE_PITCH
    while y < box.bottom - 0.15:
        plotter.line(box.x, y, box.right, y, stroke_width=RULE, stroke_gray=RULE_C)
        y += LINE_PITCH


def paint_lined_page(
    plotter: Plotter,
    device: Device,
    pad: LinedPad,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Single-face full-bleed lined page. No header, holes, or chrome."""
    _bound_ramp(plotter, ramp)
    paint_lines(plotter, device.page_rect())


@dataclass(frozen=True, slots=True)
class PerspectiveGrid:
    """Full-bleed square mesh. The page center is the center of a cell."""

    pitch: float
    cx: float
    cy: float
    verticals: tuple[float, ...]
    horizontals: tuple[float, ...]
    falloff_left: float
    falloff_right: float
    falloff_top: float
    falloff_bottom: float


@dataclass(frozen=True, slots=True)
class PerspectiveRay:
    """One ray from the page center to the page boundary."""

    x1: float
    y1: float
    x2: float
    y2: float
    gray: float


def _axis_lines(lo: float, hi: float, center: float, pitch: float) -> tuple[float, ...]:
    """Positions ``center ± pitch/2 + k·pitch`` that still lie in ``[lo, hi]``."""
    lines: list[float] = []
    k = 0
    while True:
        step = (k + 0.5) * pitch
        hit = False
        for pos in (center - step, center + step):
            if lo <= pos <= hi:
                lines.append(pos)
                hit = True
        if not hit:
            break
        k += 1
    lines.sort()
    return tuple(lines)


def _edge_falloff(
    lo: float, hi: float, center: float, lines: tuple[float, ...]
) -> tuple[float, float]:
    """Partial square outside the outermost lines. Equal when ``center`` is mid-span."""
    if not lines:
        return center - lo, hi - center
    return lines[0] - lo, hi - lines[-1]


# This page only. Engineering and dotgrid keep their own pitches. Not a TOML knob.
PERSPECTIVE_PITCH_MM = 7.0


def perspective_grid(
    page: Rect, *, pitch: float = PERSPECTIVE_PITCH_MM
) -> PerspectiveGrid:
    """Square grid across ``page``, vanishing point in the middle of a cell.

    Vertical lines are at ``cx ± pitch/2 + k·pitch`` and horizontal lines at
    ``cy ± pitch/2 + k·pitch``, for every integer ``k`` whose line still
    meets the page. ``cx, cy`` is the center of ``page``. That placement
    makes the leftover partial square on the left equal the one on the
    right, and the top leftover equal the bottom leftover.
    """
    cx = page.x + page.w / 2
    cy = page.y + page.h / 2
    verticals = _axis_lines(page.x, page.right, cx, pitch)
    horizontals = _axis_lines(page.y, page.bottom, cy, pitch)
    falloff_left, falloff_right = _edge_falloff(page.x, page.right, cx, verticals)
    falloff_top, falloff_bottom = _edge_falloff(page.y, page.bottom, cy, horizontals)
    return PerspectiveGrid(
        pitch,
        cx,
        cy,
        verticals,
        horizontals,
        falloff_left,
        falloff_right,
        falloff_top,
        falloff_bottom,
    )


# Equal-angle fan. Not a Spec/TOML knob. 360/5 = 72 rays, 36 chords.
PERSPECTIVE_RAY_STEP_DEG = 5.0


def _ray_direction(k: int) -> tuple[float, float]:
    """Unit step at ``θ = k · PERSPECTIVE_RAY_STEP_DEG``.

    ``θ = 0`` points along +x. Angles increase counterclockwise in
    mathematical coordinates, so page-down ``y`` uses ``−sin θ``.
    """
    theta = math.radians(k * PERSPECTIVE_RAY_STEP_DEG)
    dx = math.cos(theta)
    dy = -math.sin(theta)
    if abs(dx) < 1e-12:
        dx = 0.0
    if abs(dy) < 1e-12:
        dy = 0.0
    return dx, dy


def _ray_hit(
    page: Rect, cx: float, cy: float, dx: float, dy: float
) -> tuple[float, float]:
    """Where the ray from ``(cx, cy)`` along ``(dx, dy)`` meets the page edge."""
    times: list[float] = []
    if dx > 0:
        times.append((page.right - cx) / dx)
    elif dx < 0:
        times.append((page.x - cx) / dx)
    if dy > 0:
        times.append((page.bottom - cy) / dy)
    elif dy < 0:
        times.append((page.y - cy) / dy)
    t = min(times)
    x = min(page.right, max(page.x, cx + t * dx))
    y = min(page.bottom, max(page.y, cy + t * dy))
    return x, y


def perspective_rays(page: Rect) -> tuple[PerspectiveRay, ...]:
    """Equal-angle rays from the page center, clipped to the page.

    ``θ = k · 5°`` for ``k = 0 … 71`` (a full turn). Each stroke runs from
    the vanishing point to the first page edge in that direction. Opposite
    rays (``k`` and ``k + 36``) are one chord through the center, so the
    fan is 36 chords. ``k`` even is ``MUTED`` (0°, 10°, 20°…); ``k`` odd
    is ``GHOST`` (5°, 15°…). ``0°`` and ``90°`` pass through the middle of
    the center cell, parallel to the grid.
    """
    cx = page.x + page.w / 2
    cy = page.y + page.h / 2
    count = int(round(360 / PERSPECTIVE_RAY_STEP_DEG))
    rays: list[PerspectiveRay] = []
    for k in range(count):
        dx, dy = _ray_direction(k)
        x2, y2 = _ray_hit(page, cx, cy, dx, dy)
        gray = MUTED if k % 2 == 0 else GHOST
        rays.append(PerspectiveRay(cx, cy, x2, y2, gray))
    return tuple(rays)


def paint_perspective_page(
    plotter: Plotter,
    device: Device,
    pad: PerspectivePad,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Single-face full-bleed perspective page. No header, frame, or margin."""
    _bound_ramp(plotter, ramp)
    page = device.page_rect()
    grid = perspective_grid(page)
    for x in grid.verticals:
        plotter.line(x, page.y, x, page.bottom, stroke_width=RULE, stroke_gray=RULE_C)
    for y in grid.horizontals:
        plotter.line(page.x, y, page.right, y, stroke_width=RULE, stroke_gray=RULE_C)
    for ray in perspective_rays(page):
        plotter.line(
            ray.x1, ray.y1, ray.x2, ray.y2, stroke_width=RULE, stroke_gray=ray.gray
        )


def _paint_steno_dots(plotter: Plotter, x0: float, x1: float, y: float) -> None:
    """Black flat dots along one horizontal. Fixed pitch, no Spec knob."""
    span = x1 - x0
    i = 0
    while i * STENO_DOT_PITCH_MM + STENO_DOT_W_MM <= span + 1e-9:
        plotter.rect(
            Rect(
                x0 + i * STENO_DOT_PITCH_MM,
                y - STENO_DOT_H_MM / 2,
                STENO_DOT_W_MM,
                STENO_DOT_H_MM,
            ),
            stroke=False,
            fill=True,
            fill_gray=INK,
        )
        i += 1


def _paint_steno_ruling(plotter: Plotter, device: Device) -> None:
    """Close black dots in the content-frame field; solid center past them."""
    field = steno_horizontal_field(device)
    ruling = steno_ruling(field)
    grid = ruling.origin
    for i in range(ruling.n_lines):
        y = grid.y + i * ruling.pitch
        _paint_steno_dots(plotter, grid.x, grid.right, y)
    y0, y1 = _steno_center_ys(device, field)
    plotter.line(
        device.page_width / 2,
        y0,
        device.page_width / 2,
        y1,
        stroke_width=HAIR,
        stroke_gray=INK,
    )
