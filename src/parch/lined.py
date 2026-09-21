"""Edge-to-edge lined pages. Pad-only has no cover; a notebook may prefix one."""

import parch.sections.kinds as kinds
from parch.components.lined import LinedPad
from parch.sections.page import Page
from parch.spec import Spec


def lined_pages(spec: Spec) -> list[Page]:
    """One full-bleed lined face per ``lined_sheets``. Empty when 0.

    Exclusive pad-only when this count is > 0 on year-planner and
    other pad counts stay 0. Year-planner mix with engineering /
    steno / dotgrid raises ``ConfigError`` — this helper stays empty-safe.
    """
    built: list[Page] = []
    for sheet in range(1, spec.lined_sheets + 1):
        built.append(
            Page(
                dest=spec.dest_for_lined_pad(sheet),
                kind=kinds.Lined(),
                title="Lined",
                nav=(),
                components=(LinedPad(sheet=sheet, sheets=spec.lined_sheets),),
            )
        )
    return built
