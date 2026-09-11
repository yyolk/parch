"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

Unmigrated painters still pass ``face`` + ``bold``. That path is not a
plotter secret: ``FaceBridge`` (owned by the ramp) maps
``(face, bold, size)`` → ``TypeInk``. ``Fpdf2Plotter`` asks
``ramp.resolve_face(...)`` when ``family`` is omitted. Cover / header stay
on roles. Dual path is intentional until those painters adopt roles.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
and every face bridge resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome"]
type TypeFace = Literal["sans", "serif"]


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


# Unmigrated face+bold → curated Jost cut. Weight override is not in the
# table — ``FaceBridge.resolve`` applies it before lookup. Size is carried
# onto the ink; it is not a weight axis today.
_FACE: dict[tuple[TypeFace, bool], TypeWeight] = {
    ("serif", False): "medium",
    ("serif", True): "medium",
    ("sans", False): "book",
    ("sans", True): "bold",
}


@dataclass(frozen=True, slots=True)
class FaceBridge:
    """Explicit ``(face, bold, size)`` → ``TypeInk``. Same catalog as the ramp.

    Pure table + catalog lookup. No I/O, no ambient container. Serif maps
    to Medium (the old Liberation Serif stand-in); sans regular is Book;
    sans bold is Bold. An explicit ``weight`` wins over face+bold.
    """

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def resolve(
        self,
        face: TypeFace,
        bold: bool,
        size: float,
        *,
        weight: TypeWeight | None = None,
    ) -> TypeInk:
        cut = weight if weight is not None else _FACE[(face, bold)]
        ink = TypeInk(family="jost", weight=cut, size=size)
        self.catalog.path(ink.family, ink.weight)
        return ink


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, role: TypeRole) -> TypeInk:
        """Resolve a closed type role to plotter-ready ink."""
        ...

    def resolve_face(
        self,
        face: TypeFace,
        bold: bool,
        size: float,
        *,
        weight: TypeWeight | None = None,
    ) -> TypeInk:
        """Resolve an unmigrated face+bold path to plotter-ready ink."""
        ...


_JOST: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map + face bridge. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        ink = _JOST[role]
        self.catalog.path(ink.family, ink.weight)
        return ink

    def resolve_face(
        self,
        face: TypeFace,
        bold: bool,
        size: float,
        *,
        weight: TypeWeight | None = None,
    ) -> TypeInk:
        return FaceBridge(self.catalog).resolve(face, bold, size, weight=weight)
