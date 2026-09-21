"""Duplex lined/dotgrid pad — one front + one back page per sheet."""

from typing import Literal

import parch.sections.kinds as kinds
from parch.components.dotgrid import DotGridPad
from parch.components.lined import LinedPad
from parch.sections.page import Page, PageKind
from parch.spec import Spec

type PairOrder = Literal["lined-dotgrid", "dotgrid-lined"]


class LinedDotGridPadSection:
    """Emit duplex pair faces. Front kind is the first name token."""

    def __init__(self, spec: Spec, order: PairOrder = "lined-dotgrid") -> None:
        self.spec = spec
        self.order = order

    def pages(self) -> list[Page]:
        spec = self.spec
        sheets = (
            spec.lined_dotgrid_sheets
            if self.order == "lined-dotgrid"
            else spec.dotgrid_lined_sheets
        )
        front_kind, back_kind = (
            (kinds.Lined(), kinds.Dotgrid())
            if self.order == "lined-dotgrid"
            else (kinds.Dotgrid(), kinds.Lined())
        )
        built: list[Page] = []
        for sheet in range(1, sheets + 1):
            built.append(
                _pair_page(spec, self.order, sheet, sheets, "front", front_kind)
            )
            built.append(_pair_page(spec, self.order, sheet, sheets, "back", back_kind))
        return built


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
