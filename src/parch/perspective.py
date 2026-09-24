"""Edge-to-edge perspective pages. Pad-only has no cover; a notebook may prefix one."""

from parch.components.perspective import PerspectivePad
from parch.sections.page import Page
from parch.spec import Spec


def perspective_pages(spec: Spec) -> list[Page]:
    """One full-bleed perspective face per ``perspective_sheets``. Empty when 0.

    Exclusive pad-only when this count is > 0 on year-planner and
    other pad counts stay 0. Year-planner mix with engineering /
    steno / dotgrid / lined raises ``ConfigError``.
    """
    built: list[Page] = []
    for sheet in range(1, spec.perspective_sheets + 1):
        built.append(
            Page(
                dest=spec.dest_for_perspective_pad(sheet),
                kind="perspective",
                title="Perspective",
                nav=(),
                components=(
                    PerspectivePad(sheet=sheet, sheets=spec.perspective_sheets),
                ),
            )
        )
    return built
