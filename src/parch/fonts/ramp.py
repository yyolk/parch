"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
resolves to ``family="jost"``.

Thesis I — context cascade
--------------------------
``TypeContext`` is a frozen snapshot of page/section defaults (body / chrome
slots). ``PlannerLayout`` owns an explicit stack (push / pop / context
manager) and binds a frozen snapshot into the ramp handed to painters.
``ink(role)`` merges the role map **over** the current context: role-specified
fields win; unspecified role fields inherit from the stacked snapshot.
No threadlocals, no ``contextvars``.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol, Self

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome", "body"]


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


@dataclass(frozen=True, slots=True)
class TypePatch:
    """Partial ink. ``None`` means inherit from the layer below."""

    family: TypeFamily | None = None
    weight: TypeWeight | None = None
    size: float | None = None

    def merge_over(self, below: Self) -> Self:
        """Self over ``below`` — specified fields win."""
        return TypePatch(
            family=below.family if self.family is None else self.family,
            weight=below.weight if self.weight is None else self.weight,
            size=below.size if self.size is None else self.size,
        )

    def resolve(self) -> TypeInk:
        if self.family is None or self.weight is None or self.size is None:
            raise ValueError(f"incomplete type ink: {self}")
        return TypeInk(family=self.family, weight=self.weight, size=self.size)


@dataclass(frozen=True, slots=True)
class TypeContext:
    """Frozen page/section defaults. Later stack frames overlay earlier ones."""

    body: TypePatch = TypePatch()
    chrome: TypePatch = TypePatch()

    def overlay(self, above: Self) -> Self:
        """``above`` wins field-wise; unspecified fields inherit."""
        return TypeContext(
            body=above.body.merge_over(self.body),
            chrome=above.chrome.merge_over(self.chrome),
        )

    def slot(self, role: TypeRole) -> TypePatch:
        match role:
            case "body":
                return self.body
            case "chrome":
                return self.chrome
            case _:
                return TypePatch()


# Root snapshot owned by PlannerLayout. Body/chrome roles omit size so a
# page push can change them without exploding the role set.
ROOT_CONTEXT = TypeContext(
    body=TypePatch(size=8.5),
    chrome=TypePatch(size=7.4),
)

# Role map — complete roles pin every field (context cannot shrink cover_year).
# body / chrome pin family+weight only; size comes from the stacked context.
_JOST: dict[TypeRole, TypePatch] = {
    "cover_year": TypePatch(family="jost", weight="heavy", size=42),
    "cover_brow": TypePatch(family="jost", weight="medium", size=10),
    "page_title": TypePatch(family="jost", weight="medium", size=11),
    "chrome": TypePatch(family="jost", weight="book"),
    "body": TypePatch(family="jost", weight="book"),
}


def merge_role_over_context(role: TypeRole, context: TypeContext) -> TypeInk:
    """Role map over the current context. Role-specified fields win."""
    return _JOST[role].merge_over(context.slot(role)).resolve()


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, role: TypeRole) -> TypeInk:
        """Resolve a closed type role to plotter-ready ink."""
        ...

    def bind(self, context: TypeContext) -> "BoundRamp":
        """Freeze ``context`` onto a painter-facing ramp view."""
        ...


@dataclass(frozen=True, slots=True)
class BoundRamp:
    """Painter-facing ramp: ``ink(role)`` merges the role map over a snapshot.

    The snapshot is frozen at bind time — later layout pushes do not leak in.
    """

    catalog: FontCatalog
    context: TypeContext
    _roles: dict[TypeRole, TypePatch] = field(default_factory=lambda: dict(_JOST))

    def ink(self, role: TypeRole) -> TypeInk:
        ink = self._roles[role].merge_over(self.context.slot(role)).resolve()
        self.catalog.path(ink.family, ink.weight)
        return ink

    def bind(self, context: TypeContext) -> Self:
        return BoundRamp(catalog=self.catalog, context=context, _roles=self._roles)


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole, context: TypeContext | None = None) -> TypeInk:
        """Merge ``_JOST[role]`` over ``context`` (default ``ROOT_CONTEXT``)."""
        snap = ROOT_CONTEXT if context is None else context
        ink = merge_role_over_context(role, snap)
        self.catalog.path(ink.family, ink.weight)
        return ink

    def bind(self, context: TypeContext) -> BoundRamp:
        return BoundRamp(catalog=self.catalog, context=context)
