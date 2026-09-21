"""Edge-to-edge clone-dot pages. Pad-only has no cover; ``DotGridNotebook`` prefixes one."""

import parch.sections.kinds as kinds
from parch.components.dotgrid import DotGridPad
from parch.sections.page import Page
from parch.spec import Spec


def dotgrid_pages(spec: Spec) -> list[Page]:
    """One full-bleed clone-dot face per ``dotgrid_sheets``. Empty when 0.

    Press concatenates this after engineering/steno when those counts
    are also set (P5 compose). Exclusive when only this count is > 0.
    """
    built: list[Page] = []
    for sheet in range(1, spec.dotgrid_sheets + 1):
        built.append(
            Page(
                dest=spec.dest_for_dotgrid_pad(sheet),
                kind=kinds.Dotgrid(),
                title="Dot grid",
                nav=(),
                components=(DotGridPad(sheet=sheet, sheets=spec.dotgrid_sheets),),
            )
        )
    return built
