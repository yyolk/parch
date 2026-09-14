"""Engineering pad: layout seats first, then a thin painter.

Header fields and the 5×5 major/minor grid are ``rows`` / ``columns``
tracks — not a freehand paint dump. Front inks header + blank well;
back inks the grid on the full frame. No holes, no hole-margin strip.
"""

from dataclasses import dataclass

from parch.components.engineering import EngineeringPad
from parch.fonts.ramp import TypeRamp, TypeRef
from parch.geom import Rect
from parch.layouts.planner.painters import (
    HAIR,
    MUTED,
    RULE,
    RULE_C,
    _bound_ramp,
    _ink_text,
)
from parch.plotter.protocol import Plotter
from parch.tracks import columns, rows

ENG_HEADER_ROW_H = 6.4
ENG_HEADER_H = ENG_HEADER_ROW_H * 3
ENG_HEAD_WEIGHTS = (0.68, 0.32)
ENG_FIELD_GAP = 2.2
ENG_INSET_X = 1.4
ENG_INSET_Y = 0.55
ENG_LABEL_TITLE = 12.0
ENG_LABEL_NO = 8.0
ENG_LABEL_NAME = 12.0
ENG_LABEL_DATE = 10.0
ENG_LABEL_SUBJECT = 16.0
ENG_LABEL_SHEET = 16.0
ENG_MAJOR = 5
ENG_TARGET_PITCH = 5.0
ENG_MIN_PITCH = 2.0


@dataclass(frozen=True, slots=True)
class EngineeringPadSeats:
    """Front geometry: three header rows + blank writing well."""

    frame: Rect
    title: Rect
    number: Rect
    name: Rect
    date: Rect
    subject: Rect
    sheet: Rect
    well: Rect


@dataclass(frozen=True, slots=True)
class EngineeringGridSeats:
    """Back geometry: square minor cells; major every ``ENG_MAJOR``."""

    box: Rect
    columns: tuple[Rect, ...]
    rows: tuple[Rect, ...]


def engineering_pad_seats(frame: Rect) -> EngineeringPadSeats:
    """Split *frame* into header field seats and a flex writing well."""
    header_h = min(ENG_HEADER_H, max(frame.h * 0.18, ENG_HEADER_ROW_H))
    header, well = rows(
        frame,
        2,
        gap=0,
        weights=(header_h, max(frame.h - header_h, 1)),
    )
    top, mid, bottom = rows(header, 3)
    title, number = columns(top, 2, gap=ENG_FIELD_GAP, weights=ENG_HEAD_WEIGHTS)
    name, date = columns(mid, 2, gap=ENG_FIELD_GAP, weights=ENG_HEAD_WEIGHTS)
    subject, sheet = columns(bottom, 2, gap=ENG_FIELD_GAP, weights=ENG_HEAD_WEIGHTS)
    return EngineeringPadSeats(
        frame=frame,
        title=title,
        number=number,
        name=name,
        date=date,
        subject=subject,
        sheet=sheet,
        well=well,
    )


def engineering_grid_counts(box: Rect, *, cluster: int = ENG_MAJOR) -> tuple[int, int]:
    """Largest cluster-aligned square tiling that fits *box*."""
    if box.w < ENG_MIN_PITCH or box.h < ENG_MIN_PITCH:
        return cluster, cluster
    n_cols = max(cluster, (int(box.w / ENG_TARGET_PITCH) // cluster) * cluster)
    pitch = box.w / n_cols
    n_rows = max(cluster, (int(box.h / pitch) // cluster) * cluster)
    return n_cols, n_rows


def engineering_grid_seats(box: Rect) -> EngineeringGridSeats:
    """Square ``columns`` × ``rows`` seats, centered; counts are multiples of 5."""
    n_cols, n_rows = engineering_grid_counts(box)
    pitch = min(box.w / n_cols, box.h / n_rows)
    grid_w = n_cols * pitch
    grid_h = n_rows * pitch
    grid = Rect(
        box.x + (box.w - grid_w) / 2,
        box.y + (box.h - grid_h) / 2,
        grid_w,
        grid_h,
    )
    return EngineeringGridSeats(
        box=grid,
        columns=columns(grid, n_cols),
        rows=rows(grid, n_rows),
    )


def paint_engineering_pad(
    plotter: Plotter,
    frame: Rect,
    pad: EngineeringPad,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Dispatch one duplex face. Front never grids; back never headers."""
    match pad.face:
        case "front":
            paint_engineering_front(plotter, frame, pad, ramp=ramp)
        case "back":
            paint_engineering_back(plotter, frame, pad, ramp=ramp)


def paint_engineering_front(
    plotter: Plotter,
    frame: Rect,
    _pad: EngineeringPad,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """Header write-ins + blank well + outer rules. No grid."""
    _bound_ramp(plotter, ramp)
    seats = engineering_pad_seats(frame)
    _paint_outer(plotter, seats.frame)
    _paint_field(plotter, seats.title, "Title", ENG_LABEL_TITLE)
    _paint_field(plotter, seats.number, "No.", ENG_LABEL_NO)
    _paint_field(plotter, seats.name, "Name", ENG_LABEL_NAME)
    _paint_field(plotter, seats.date, "Date", ENG_LABEL_DATE)
    _paint_field(plotter, seats.subject, "Subject", ENG_LABEL_SUBJECT)
    _paint_sheet_field(plotter, seats.sheet)
    plotter.line(
        seats.well.x,
        seats.well.y,
        seats.well.right,
        seats.well.y,
        stroke_width=HAIR,
        stroke_gray=MUTED,
    )


def paint_engineering_back(
    plotter: Plotter,
    frame: Rect,
    _pad: EngineeringPad,
    *,
    ramp: TypeRamp | None = None,
) -> None:
    """5×5 major/minor square grid + outer rules. No header."""
    _bound_ramp(plotter, ramp)
    _paint_outer(plotter, frame)
    seats = engineering_grid_seats(frame)
    _paint_grid(plotter, seats)


def _paint_outer(plotter: Plotter, frame: Rect) -> None:
    plotter.rect(
        frame,
        stroke=True,
        fill=False,
        stroke_width=HAIR,
        stroke_gray=MUTED,
    )


def _paint_field(plotter: Plotter, box: Rect, label: str, label_w: float) -> None:
    inner = box.inset(ENG_INSET_X, ENG_INSET_Y)
    tag, write = inner.split_left(min(label_w, inner.w * 0.45))
    _ink_text(
        plotter,
        tag,
        label,
        TypeRef(step="label"),
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    plotter.line(
        write.x,
        write.bottom,
        write.right,
        write.bottom,
        stroke_width=RULE,
        stroke_gray=RULE_C,
    )


def _paint_sheet_field(plotter: Plotter, box: Rect) -> None:
    """``Sheet ____ of ____`` — two write-ins, not a filled number."""
    inner = box.inset(ENG_INSET_X, ENG_INSET_Y)
    label_w = min(ENG_LABEL_SHEET, inner.w * 0.34)
    tag, rest = inner.split_left(label_w)
    _ink_text(
        plotter,
        tag,
        "Sheet",
        TypeRef(step="label"),
        gray=MUTED,
        small_caps=True,
        align="left",
    )
    write, of_rest = columns(rest, 2, gap=1.6, weights=(0.42, 0.58))
    of_tag, of_write = of_rest.split_left(min(6.0, of_rest.w * 0.35))
    _ink_text(
        plotter,
        of_tag,
        "of",
        TypeRef(step="label"),
        gray=MUTED,
        small_caps=True,
        align="center",
    )
    for stroke in (write, of_write):
        plotter.line(
            stroke.x,
            stroke.bottom,
            stroke.right,
            stroke.bottom,
            stroke_width=RULE,
            stroke_gray=RULE_C,
        )


def _paint_grid(plotter: Plotter, seats: EngineeringGridSeats) -> None:
    box = seats.box
    xs = [col.x for col in seats.columns] + [seats.columns[-1].right]
    ys = [band.y for band in seats.rows] + [seats.rows[-1].bottom]
    for i, x in enumerate(xs):
        major = i % ENG_MAJOR == 0
        plotter.line(
            x,
            box.y,
            x,
            box.bottom,
            stroke_width=HAIR if major else RULE,
            stroke_gray=MUTED if major else RULE_C,
        )
    for i, y in enumerate(ys):
        major = i % ENG_MAJOR == 0
        plotter.line(
            box.x,
            y,
            box.right,
            y,
            stroke_width=HAIR if major else RULE,
            stroke_gray=MUTED if major else RULE_C,
        )
