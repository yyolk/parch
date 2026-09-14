"""Single-page Gregg / stenographer pad — no header, no holes, not duplex."""

from parch.components.gregg import GreggPad
from parch.sections.page import Page
from parch.spec import Spec


class GreggPadSection:
    """Emit single Gregg faces. Demo-only press when ``gregg_pages > 0``."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        return [
            Page(
                dest=spec.dest_for_gregg_pad(page),
                kind="gregg",
                title="Gregg",
                nav=(),
                components=(GreggPad(page=page),),
            )
            for page in range(1, spec.gregg_pages + 1)
        ]
