"""Duplex engineering pad — one front + one back. Section builds the pair."""

from parch.components import EngineeringPad
from parch.sections.page import Page
from parch.spec import Spec


class EngineeringPadSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        front = spec.dest_for_engineering_pad("front")
        back = spec.dest_for_engineering_pad("back")
        title = "Engineering"
        return [
            Page(
                dest=front,
                kind="engineering_pad",
                title=title,
                nav=(),
                components=(
                    EngineeringPad(
                        face="front",
                        year=spec.year,
                        title=title,
                        other_dest=back,
                    ),
                ),
            ),
            Page(
                dest=back,
                kind="engineering_pad",
                title=title,
                nav=(),
                components=(
                    EngineeringPad(
                        face="back",
                        year=spec.year,
                        title=title,
                        other_dest=front,
                    ),
                ),
            ),
        ]
