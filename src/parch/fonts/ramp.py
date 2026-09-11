"""Size-band type: painters pass size; the ramp picks the Jost cut.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call
``ramp.ink(size, role=..., bold=...)`` and pass those fields through; they do
not think in sans/serif slots.

A small role set (``cover_year``, ``page_title``, ``chrome``) pins weight for
intentional exceptions. Everything else walks the ramp's size→weight band
table. ``bold=True`` forces the Bold cut only inside body bands (medium /
book) — the display band stays Heavy.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every path
resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Mapping, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal["cover_year", "page_title", "chrome"]


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


# First match wins. Display (≥30) is Heavy; titles (≥11) Medium; else Book.
SIZE_BANDS: tuple[tuple[float, TypeWeight], ...] = (
    (30.0, "heavy"),
    (11.0, "medium"),
    (0.0, "book"),
)

# Role overrides pin weight regardless of size or bold.
ROLE_WEIGHTS: Mapping[TypeRole, TypeWeight] = MappingProxyType(
    {
        "cover_year": "heavy",
        "page_title": "medium",
        "chrome": "book",
    }
)

_BODY_BANDS: frozenset[TypeWeight] = frozenset({"book", "medium"})


class TypeRamp(Protocol):
    catalog: FontCatalog
    bands: tuple[tuple[float, TypeWeight], ...]
    roles: Mapping[TypeRole, TypeWeight]

    def ink(
        self,
        size: float,
        *,
        role: TypeRole | None = None,
        bold: bool = False,
    ) -> TypeInk:
        """Resolve size (+ optional role / bold) to plotter-ready ink."""
        ...


def band_weight(
    size: float,
    bands: tuple[tuple[float, TypeWeight], ...] = SIZE_BANDS,
) -> TypeWeight:
    """Pure table walk — first floor the size meets."""
    for floor, weight in bands:
        if size >= floor:
            return weight
    raise ValueError(f"no size band for {size}")


def cut_for(
    size: float,
    *,
    role: TypeRole | None = None,
    bold: bool = False,
    bands: tuple[tuple[float, TypeWeight], ...] = SIZE_BANDS,
    roles: Mapping[TypeRole, TypeWeight] = ROLE_WEIGHTS,
) -> TypeWeight:
    """Role override, else size band; bold forces Bold inside body bands."""
    match role:
        case None:
            weight = band_weight(size, bands)
            match (weight, bold):
                case (band, True) if band in _BODY_BANDS:
                    return "bold"
                case (band, _):
                    return band
        case pinned:
            return roles[pinned]


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Jost-only catalog + explicit size-band table. Default — and only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)
    bands: tuple[tuple[float, TypeWeight], ...] = SIZE_BANDS
    roles: Mapping[TypeRole, TypeWeight] = field(default=ROLE_WEIGHTS)

    def ink(
        self,
        size: float,
        *,
        role: TypeRole | None = None,
        bold: bool = False,
    ) -> TypeInk:
        weight = cut_for(size, role=role, bold=bold, bands=self.bands, roles=self.roles)
        ink = TypeInk(family="jost", weight=weight, size=size)
        self.catalog.path(ink.family, ink.weight)
        return ink
