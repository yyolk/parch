"""Duplex computation pad — one sheet is front then back. Not a book."""

from parch.components.pad import PadFace
from parch.sections.page import Page
from parch.spec import Spec


class PadSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.pad_pages + 1):
            for face in ("front", "back"):
                built.append(
                    Page(
                        dest=spec.dest_for_pad(sheet, face),
                        kind="pad_front" if face == "front" else "pad_back",
                        title="Pad",
                        nav=(),
                        components=(
                            PadFace(
                                year=spec.year,
                                sheet=sheet,
                                sheets=spec.pad_pages,
                                face=face,
                                grid_pitch_mm=spec.pad_grid_pitch_mm,
                                major_every=spec.pad_major_every,
                                header=spec.pad_header,
                            ),
                        ),
                    )
                )
        return built
