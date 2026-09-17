"""Nomad check-off pack/type proofs. Circle + diamond-every-10th only.

Product press is dense pack + 0.90× micro (``CHECKOFF_DEFAULT`` /
``checkoff_var_dense_text_larger``). This matrix is replay only — not a Spec
knob. Run: ``uv run python scripts/checkoff_pack_proofs.py -o dest``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from parch.components import Checkoff365
from parch.devices import NOMAD
from parch.fonts.ramp import EffectiveRamp
from parch.layouts.planner.painters import (
    CHECKOFF_DEFAULT,
    CheckoffStyle,
    checkoff_columns,
    checkoff_mark,
    checkoff_numeral_ink,
    checkoff_seats,
    paint_checkoff_365,
    paint_header,
    paint_nav,
    strip_active,
    strip_items,
    well_rect,
)
from parch.plotter.fpdf2 import Fpdf2Plotter
from parch.sections.checkoff import Checkoff365Section
from parch.spec import Spec
from parch.specimen import render_page_png

DENSE = CheckoffStyle(gap=0.30, mark_frac=0.91, col_pref=16, col_penalty=0.08)
MID = CheckoffStyle(gap=0.55, mark_frac=0.84, col_pref=16, col_penalty=0.22)

VARIANTS: tuple[tuple[str, CheckoffStyle], ...] = (
    (
        "checkoff_var_dense_text_current",
        CheckoffStyle(
            gap=DENSE.gap,
            mark_frac=DENSE.mark_frac,
            col_pref=DENSE.col_pref,
            col_penalty=DENSE.col_penalty,
            numeral_scale=0.74,
            label_inset=0.20,
        ),
    ),
    (
        # Locked as CHECKOFF_DEFAULT / product press.
        "checkoff_var_dense_text_larger",
        CHECKOFF_DEFAULT,
    ),
    (
        "checkoff_var_dense_text_smaller",
        CheckoffStyle(
            gap=DENSE.gap,
            mark_frac=DENSE.mark_frac,
            col_pref=DENSE.col_pref,
            col_penalty=DENSE.col_penalty,
            numeral_scale=0.58,
            label_inset=0.24,
        ),
    ),
    (
        "checkoff_var_mid_text_current",
        CheckoffStyle(
            gap=MID.gap,
            mark_frac=MID.mark_frac,
            col_pref=MID.col_pref,
            col_penalty=MID.col_penalty,
            numeral_scale=0.74,
            label_inset=0.20,
        ),
    ),
)


def _describe(name: str, style: CheckoffStyle) -> str:
    well = well_rect(NOMAD)
    cols = checkoff_columns(well, 365, style)
    mark = checkoff_mark(checkoff_seats(well, 365, style)[0], style)
    ink = checkoff_numeral_ink(EffectiveRamp(), style)
    return (
        f"{name}: cols={cols} gap={style.gap:g} mark_frac={style.mark_frac:g} "
        f"mark={mark.w:.2f}mm scale={style.numeral_scale:g} "
        f"inset={style.label_inset:g} size={float(ink.size):.2f}pt "
        f"medium MUTED circle+diamond-10"
    )


def _paint(pdf: Path, style: CheckoffStyle) -> None:
    spec = Spec(checkoff_365=True, months=(1,), notes_pages=0)
    page = Checkoff365Section(spec).pages()[0]
    sheet = next(item for item in page.components if isinstance(item, Checkoff365))
    ramp = EffectiveRamp()
    plotter = Fpdf2Plotter(NOMAD, ramp=ramp)
    dests = {page.dest, *(item.dest for item in page.nav)}
    dests.update(dest for dest in sheet.day_dests if dest)
    for dest in dests:
        plotter.reserve_dest(dest)
    plotter.begin_page()
    for dest in dests:
        plotter.add_dest(dest)
    paint_header(plotter, NOMAD, page.title, str(sheet.year), ramp=ramp)
    paint_nav(plotter, NOMAD, strip_items(page), strip_active(page.kind), ramp=ramp)
    paint_checkoff_365(plotter, well_rect(NOMAD), sheet, ramp=ramp, style=style)
    plotter.finish(pdf)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--out", type=Path, required=True)
    args = parser.parse_args(argv)
    dest: Path = args.out
    dest.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmp:
        for name, style in VARIANTS:
            pdf = Path(tmp) / f"{name}.pdf"
            _paint(pdf, style)
            render_page_png(pdf, 1, dest / f"{name}.png", dpi=192)
            print(_describe(name, style))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
