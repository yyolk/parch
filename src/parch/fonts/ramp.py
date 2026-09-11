"""Role- and slot-based type: painters ask; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.

Named roles (``cover_year``, ``cover_brow``, ``page_title``, ``chrome``)
ignore slots. Cover and header keep calling ``ramp.ink(role)``.

Everything else goes through ``ramp.resolve_slot(slot, emphasis, size)``.
``TypeSlot`` is the typed edge that used to be ``TextFace`` sans/serif —
weight policy lives here, not Liberation-era face folklore in the plotter.

``TypeInk`` carries family + weight + size. Painters pass those fields
through. ``family`` stays on the ink so a later dual-font ramp can pick
another catalog family without ripping out the plotter kwarg. Today every
role and slot resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome"]


class TypeSlot(StrEnum):
    """First-class weight-policy slot. Not a typeface family.

    ``COPY`` is running labels / chrome / dates — Book, Bold when strong.
    ``MARK`` is raised stubs / week chips / ticket numbers — Medium either way.
    Emphasis never promotes a mark; that used to hide in ``face="serif"``.
    """

    COPY = "copy"
    MARK = "mark"


class TypeEmphasis(StrEnum):
    """Strength on a slot. Roles ignore this; slots consult the table."""

    REGULAR = "regular"
    STRONG = "strong"


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

    def resolve_slot(self, slot: TypeSlot, emphasis: TypeEmphasis, size: float) -> TypeInk:
        """Map slot + emphasis + size to plotter-ready ink."""
        ...


_JOST_ROLES: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
}

# Size is an input so a later ramp can vary cuts by measure. Jost passes it through.
_JOST_SLOTS: dict[tuple[TypeSlot, TypeEmphasis], TypeWeight] = {
    (TypeSlot.COPY, TypeEmphasis.REGULAR): "book",
    (TypeSlot.COPY, TypeEmphasis.STRONG): "bold",
    (TypeSlot.MARK, TypeEmphasis.REGULAR): "medium",
    (TypeSlot.MARK, TypeEmphasis.STRONG): "medium",
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role + slot map. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        ink = _JOST_ROLES[role]
        self.catalog.path(ink.family, ink.weight)
        return ink

    def resolve_slot(self, slot: TypeSlot, emphasis: TypeEmphasis, size: float) -> TypeInk:
        weight = _JOST_SLOTS[(slot, emphasis)]
        ink = TypeInk(family="jost", weight=weight, size=size)
        self.catalog.path(ink.family, ink.weight)
        return ink
