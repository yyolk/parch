"""Duplex lined/dot-grid pad — one front + one back page per sheet."""

from typing import Literal

from parch.components.dotgrid import DotGridPad
from parch.components.lined import LinedPad
from parch.sections.page import Page, PageKind
from parch.spec import Spec

type PairOrder = Literal["lined-dot-grid", "dot-grid-lined"]


class LinedDotGridPadSection:
    """Emit duplex pair faces. Front kind is the first name token."""

    def __init__(self, spec: Spec, order: PairOrder = "lined-dot-grid") -> None:
        self.spec = spec
        self.order = order

    def pages(self) -> list[Page]:
        spec = self.spec
        sheets = (
            spec.lined_dot_grid_sheets
            if self.order == "lined-dot-grid"
            else spec.dot_grid_lined_sheets
        )
        front_kind, back_kind = (
            ("lined", "dotgrid")
            if self.order == "lined-dot-grid"
            else ("dotgrid", "lined")
        )
        built: list[Page] = []
        for sheet in range(1, sheets + 1):
            built.append(
                _pair_page(spec, self.order, sheet, sheets, "front", front_kind)
            )
            built.append(_pair_page(spec, self.order, sheet, sheets, "back", back_kind))
        return built


def duplex_pair_pages(spec: Spec) -> list[Page]:
    """One type is a plain run. Two or more types zip by sheet (pair stays together)."""
    runs = [
        run
        for run in (
            LinedDotGridPadSection(spec, "lined-dot-grid").pages(),
            LinedDotGridPadSection(spec, "dot-grid-lined").pages(),
        )
        if run
    ]
    if len(runs) <= 1:
        return runs[0] if runs else []
    return _zip_sheet_runs(runs)


def _zip_sheet_runs(runs: list[list[Page]]) -> list[Page]:
    """Interleave duplex sheets. Leftover sheets from a longer run append."""
    chunks = [_sheet_chunks(run) for run in runs]
    built: list[Page] = []
    for index in range(max(len(chunk) for chunk in chunks)):
        for chunk in chunks:
            if index < len(chunk):
                built.extend(chunk[index])
    return built


def _sheet_chunks(pages: list[Page]) -> list[list[Page]]:
    return [pages[i : i + 2] for i in range(0, len(pages), 2)]


def _pair_page(
    spec: Spec,
    order: PairOrder,
    sheet: int,
    sheets: int,
    face: str,
    kind: PageKind,
) -> Page:
    dest = spec.dest_for_duplex_pair_pad(order, sheet, face)
    if kind == "lined":
        component: LinedPad | DotGridPad = LinedPad(sheet=sheet, sheets=sheets)
        title = "Lined"
    else:
        component = DotGridPad(sheet=sheet, sheets=sheets)
        title = "Dot grid"
    return Page(
        dest=dest,
        kind=kind,
        title=title,
        nav=(),
        components=(component,),
    )
