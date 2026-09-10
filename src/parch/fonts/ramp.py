"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
Plotter still takes ``face`` / ``weight`` / ``size``; the ramp fills those kwargs.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

from parch.plotter.protocol import TextFace, TextWeight

type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome"]


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved face / weight / size — the type fields ``Plotter.text`` already takes."""

    face: TextFace
    weight: TextWeight
    size: float


class TypeRamp(Protocol):
    def ink(self, role: TypeRole) -> TypeInk:
        """Resolve a closed type role to plotter-ready ink."""
        ...


_JOST: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(face="serif", weight="heavy", size=42),
    "cover_brow": TypeInk(face="serif", weight="medium", size=10),
    "page_title": TypeInk(face="serif", weight="medium", size=11),
    "chrome": TypeInk(face="sans", weight="book", size=7.4),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Default Jost role map. Construct at the layout / book boundary."""

    def ink(self, role: TypeRole) -> TypeInk:
        return _JOST[role]
