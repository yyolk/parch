"""Role-based type: two small ramps, one shared Jost catalog.

Painters ask for a role; the ramp they were given resolves plotter ink.
``ChromeRamp`` covers cover / header / nav. ``BodyRamp`` covers the well.
Layout holds both and passes the relevant object — no mega-enum, no ambient
container, no signature injection, no globals.

``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type ChromeRole = Literal["cover_year", "cover_brow", "page_title", "chrome", "nav"]
type BodyRole = Literal["body", "label", "caption", "calendar_num", "strong"]


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


class ChromeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, role: ChromeRole) -> TypeInk:
        """Resolve a chrome role to plotter-ready ink."""
        ...


class BodyRamp(Protocol):
    catalog: FontCatalog

    def ink(self, role: BodyRole) -> TypeInk:
        """Resolve a body / well role to plotter-ready ink."""
        ...


_JOST_CHROME: dict[ChromeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
    "nav": TypeInk(family="jost", weight="book", size=7.6),
}

_JOST_BODY: dict[BodyRole, TypeInk] = {
    "body": TypeInk(family="jost", weight="book", size=7.0),
    "label": TypeInk(family="jost", weight="book", size=6.4),
    "caption": TypeInk(family="jost", weight="book", size=5.8),
    "calendar_num": TypeInk(family="jost", weight="bold", size=8.5),
    "strong": TypeInk(family="jost", weight="bold", size=7.2),
}


@dataclass(frozen=True, slots=True)
class JostChromeRamp:
    """Jost chrome map — cover, header slab, bottom nav."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: ChromeRole) -> TypeInk:
        ink = _JOST_CHROME[role]
        self.catalog.path(ink.family, ink.weight)
        return ink


@dataclass(frozen=True, slots=True)
class JostBodyRamp:
    """Jost body map — well copy, labels, captions, calendar numerals."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: BodyRole) -> TypeInk:
        ink = _JOST_BODY[role]
        self.catalog.path(ink.family, ink.weight)
        return ink


def jost_ramps(catalog: FontCatalog | None = None) -> tuple[JostChromeRamp, JostBodyRamp]:
    """Pair of Jost ramps sharing one catalog instance."""
    shared = jost_catalog() if catalog is None else catalog
    return JostChromeRamp(catalog=shared), JostBodyRamp(catalog=shared)
