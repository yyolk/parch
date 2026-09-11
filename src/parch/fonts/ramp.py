"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import (
    FontCatalog,
    TypeFamily,
    TypeWeight,
    jost_besley_catalog,
    jost_catalog,
    martian_besley_catalog,
)

type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome"]


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, role: TypeRole) -> TypeInk:
        """Resolve a closed type role to plotter-ready ink."""
        ...


_JOST: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
}

# Dual-font example. Chrome stays Jost Book. Titles are Besley (Regular / Bold).
# cover_year is Besley Bold — there is no vendored Besley Heavy.
_JOST_BESLEY: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="besley", weight="bold", size=42),
    "cover_brow": TypeInk(family="besley", weight="book", size=10),
    "page_title": TypeInk(family="besley", weight="bold", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map. Same visual as the pre-family Jost spike."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        return _JOST[role]


@dataclass(frozen=True, slots=True)
class JostBesleyRamp:
    """Jost chrome + Besley titles. ``cover_year`` is Besley Bold (no Heavy file)."""

    catalog: FontCatalog = field(default_factory=jost_besley_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        return _JOST_BESLEY[role]


# Martian replaces Jost as chrome. Titles stay Besley (Regular / Bold) so the
# dual-serif cover story matches JostBesleyRamp. cover_year stays Besley Bold —
# Martian has Regular + Bold only; a sans year would be Martian Bold, not Heavy.
_MARTIAN_BESLEY: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="besley", weight="bold", size=42),
    "cover_brow": TypeInk(family="besley", weight="book", size=10),
    "page_title": TypeInk(family="besley", weight="bold", size=11),
    "chrome": TypeInk(family="martian", weight="book", size=7.4),
}


@dataclass(frozen=True, slots=True)
class MartianBesleyRamp:
    """Martian chrome + Besley titles. ``cover_year`` is Besley Bold (no Heavy file)."""

    catalog: FontCatalog = field(default_factory=martian_besley_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        return _MARTIAN_BESLEY[role]
