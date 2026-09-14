"""Book surface. Structural ``pages`` / ``plot`` / ``ramp`` — not an ABC or plugin."""

from typing import Protocol

from parch.fonts.ramp import TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections.page import Page
from parch.spec import Spec


class Book(Protocol):
    """Pressable book. ``press`` calls ``plot``; ``plot`` walks ``pages``.

    YearPlanner, ProjectsNotebook, and EngineeringNotebook match this
    shape. Not a registry, ABC, or plugin hook.
    """

    ramp: TypeRamp

    def pages(self, spec: Spec) -> list[Page]:
        """Build the ordered page list for *spec*."""

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        """Reserve dests, then paint each page onto *plotter*."""
