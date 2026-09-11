"""Typographic scale: painters pick a step, not a page name.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call
``ramp.ink(step, emphasis="regular")`` and pass those fields through; they do
not think in sans/serif slots or invent one-off page roles.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every step
resolves to ``family="jost"``.

Thesis C deleted ``TypeRole`` in this PR. Old names map as:

- ``cover_year`` → ``display``
- ``cover_brow`` → ``eyebrow``
- ``page_title`` → ``title``
- ``chrome`` → ``chrome`` (same token; now a scale step, not a page role)
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeStep = Literal[
    "display",
    "title",
    "eyebrow",
    "body",
    "chrome",
    "label",
    "caption",
]
type TypeEmphasis = Literal["regular", "strong"]

# Closed ladder, largest → smallest. Every step is used by a painter.
TYPE_STEPS: tuple[TypeStep, ...] = (
    "display",
    "title",
    "eyebrow",
    "body",
    "chrome",
    "label",
    "caption",
)


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


@dataclass(frozen=True, slots=True)
class ScaleCut:
    """One closed step: a size plus the regular / strong Jost cuts."""

    size: float
    regular: TypeWeight
    strong: TypeWeight


# Audit of painter sizes, snapped to seven steps. Nearby one-offs collapse
# onto the nearest cut (6.2/6.6 → label 6.4; 7.0/7.6 → chrome 7.4;
# 5.2–5.8 → caption 5.4; 8.5 → body 8.2; 9.2 → title 11). No unused steps.
JOST_SCALE: dict[TypeStep, ScaleCut] = {
    "display": ScaleCut(size=42, regular="heavy", strong="heavy"),
    "title": ScaleCut(size=11, regular="medium", strong="bold"),
    "eyebrow": ScaleCut(size=10, regular="medium", strong="bold"),
    "body": ScaleCut(size=8.2, regular="book", strong="bold"),
    "chrome": ScaleCut(size=7.4, regular="book", strong="bold"),
    "label": ScaleCut(size=6.4, regular="book", strong="bold"),
    "caption": ScaleCut(size=5.4, regular="book", strong="bold"),
}


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        """Resolve a closed scale step (+ optional emphasis) to plotter ink."""
        ...


def scale_ink(step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
    """Look up the Jost scale table. Raises ``KeyError`` on an unknown step."""
    cut = JOST_SCALE[step]
    weight = cut.regular if emphasis == "regular" else cut.strong
    return TypeInk(family="jost", weight=weight, size=cut.size)


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost scale. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        ink = scale_ink(step, emphasis)
        self.catalog.path(ink.family, ink.weight)
        return ink
