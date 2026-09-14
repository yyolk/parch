"""Engineering / computation pad — always a front/back pair per sheet."""

from parch.components import EngineeringPadBack, EngineeringPadFront
from parch.sections.page import Page
from parch.spec import Spec


class EngineeringPadSection:
    """N sheets → 2N pages: ``engineering_pad_front`` then ``engineering_pad_back``.

    Notebook book is deferred; this section is the pressable unit.
    """

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.engineering_pad_sheets + 1):
            built.append(
                Page(
                    dest=spec.dest_for_engineering_pad_front(sheet),
                    kind="engineering_pad_front",
                    title="Engineering pad",
                    nav=(),
                    components=(
                        EngineeringPadFront(
                            year=spec.year,
                            sheet=sheet,
                            sheets=spec.engineering_pad_sheets,
                        ),
                    ),
                )
            )
            built.append(
                Page(
                    dest=spec.dest_for_engineering_pad_back(sheet),
                    kind="engineering_pad_back",
                    title="Engineering pad",
                    nav=(),
                    components=(
                        EngineeringPadBack(
                            year=spec.year,
                            sheet=sheet,
                            sheets=spec.engineering_pad_sheets,
                        ),
                    ),
                )
            )
        return built
