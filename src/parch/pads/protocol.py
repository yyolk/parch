"""Pad protocol at press/dispatch — ``pages`` + ``plot``, like Book."""

from typing import Protocol

from parch.plotter.protocol import Plotter
from parch.sections.page import Page
from parch.spec import Spec


class Pad(Protocol):
    """Press/dispatch surface: ``pages`` + ``plot``.

    Structural only — press does not ``isinstance``-check it.
    Pad-only walks have no cover. ``plot`` reserves dests, then paints.
    """

    def pages(self, spec: Spec) -> list[Page]:
        """Build the pad's pages in press order."""

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        """Reserve dests, then paint each page."""
