"""Role-free type: painters ask for steps; PageKind supplies the defaults.

Page-semantic roles explode (``daily_body``, ``week_body``, …). A single global
scale also lies: Year and Daily do not want the same body. This module is a
pure table ``PageKind → {body, chrome, title, display, brow}``.

Binding
-------
Layout calls ``ramp.for_page(kind)`` and passes the ``BoundRamp`` into painters.
Painters call ``ramp.ink(step)`` only — they never pass a kind. No threadlocals,
no ``ink(step, kind=…)`` signature injection. Optional ``weight=`` / ``size=``
override the table cell for one mark.

Cover
-----
Cover is a first-class ``PageKind`` row, not a side-channel. Cover-only marks
use the ``display`` (year) and ``brow`` (eyebrow) steps so those names stay
searchable. Interior kinds still have those keys (aliased to title / chrome)
so the table is rectangular; only cover painters ask for them.
"""

from dataclasses import dataclass, field
from typing import Literal, Mapping, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog
from parch.sections.page import PageKind

type TypeStep = Literal["body", "chrome", "title", "display", "brow"]
type TypeRole = TypeStep  # old name — steps replaced page-semantic roles

_STEPS: tuple[TypeStep, ...] = ("body", "chrome", "title", "display", "brow")


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


class TypeRamp(Protocol):
    """What painters receive: ``ink(step)``. Layout binds via ``for_page``."""

    catalog: FontCatalog

    def ink(
        self,
        step: TypeStep,
        *,
        weight: TypeWeight | None = None,
        size: float | None = None,
    ) -> TypeInk:
        """Resolve a closed type step to plotter-ready ink."""
        ...

    def for_page(self, kind: PageKind) -> TypeRamp:
        """Bind this ramp to ``kind``. Painters still see only ``ink(step)``."""
        ...


def _ink(weight: TypeWeight, size: float) -> TypeInk:
    return TypeInk(family="jost", weight=weight, size=size)


_TITLE = _ink("medium", 11)
_CHROME = _ink("book", 7.4)


def _interior(body: TypeInk) -> dict[TypeStep, TypeInk]:
    """Shared title/chrome; ``display``/``brow`` alias so the table is rectangular."""
    return {
        "title": _TITLE,
        "chrome": _CHROME,
        "body": body,
        "display": _TITLE,
        "brow": _CHROME,
    }


def jost_pagekind_table() -> dict[PageKind, dict[TypeStep, TypeInk]]:
    """Jost-only ``PageKind → step → TypeInk``. Every kind has every step."""
    return {
        "cover": {
            "title": _ink("medium", 10),
            "chrome": _CHROME,
            "body": _ink("book", 8.2),
            "display": _ink("heavy", 42),
            "brow": _ink("medium", 10),
        },
        "annual": _interior(_ink("book", 6.4)),
        "projects_index": _interior(_ink("bold", 6.6)),
        "project": _interior(_ink("bold", 6.6)),
        "meetings_index": _interior(_ink("book", 6.4)),
        "meeting": _interior(_ink("book", 6.4)),
        "tasks_index": _interior(_ink("book", 6.4)),
        "task": _interior(_ink("book", 6.4)),
        "review_index": _interior(_ink("book", 6.4)),
        "review": _interior(_ink("book", 6.4)),
        "quarter": _interior(_ink("book", 6.4)),
        "month": _interior(_ink("bold", 8.5)),
        "habits": _interior(_ink("book", 6.4)),
        "weekly": _interior(_ink("bold", 11)),
        "daily": _interior(_ink("book", 7.0)),
        "daily_notes": _interior(_ink("book", 6.4)),
    }


_JOST_PAGEKIND: dict[PageKind, dict[TypeStep, TypeInk]] = jost_pagekind_table()


def _apply_override(
    ink: TypeInk, *, weight: TypeWeight | None, size: float | None
) -> TypeInk:
    if weight is None and size is None:
        return ink
    return TypeInk(
        family=ink.family,
        weight=ink.weight if weight is None else weight,
        size=ink.size if size is None else size,
    )


@dataclass(frozen=True, slots=True)
class BoundRamp:
    """A ramp fixed to one ``PageKind``. Passed into painters — not ambient."""

    catalog: FontCatalog
    kind: PageKind
    _steps: Mapping[TypeStep, TypeInk] = field(repr=False)

    def ink(
        self,
        step: TypeStep,
        *,
        weight: TypeWeight | None = None,
        size: float | None = None,
    ) -> TypeInk:
        try:
            ink = self._steps[step]
        except KeyError as exc:
            raise KeyError(f"no step {step!r} for page kind {self.kind!r}") from exc
        resolved = _apply_override(ink, weight=weight, size=size)
        self.catalog.path(resolved.family, resolved.weight)
        return resolved

    def for_page(self, kind: PageKind) -> BoundRamp:
        return BoundRamp(
            catalog=self.catalog, kind=kind, _steps=_JOST_PAGEKIND[kind]
        )


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost PageKind table. Default — and currently only — ramp.

    ``ink(step)`` without ``for_page`` uses the cover row for ``display``/``brow``
    and the annual row for everything else. Layout always binds; prefer
    ``for_page(kind)``.
    """

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def for_page(self, kind: PageKind) -> BoundRamp:
        return BoundRamp(catalog=self.catalog, kind=kind, _steps=_JOST_PAGEKIND[kind])

    def ink(
        self,
        step: TypeStep,
        *,
        weight: TypeWeight | None = None,
        size: float | None = None,
    ) -> TypeInk:
        kind: PageKind = "cover" if step in ("display", "brow") else "annual"
        return self.for_page(kind).ink(step, weight=weight, size=size)
