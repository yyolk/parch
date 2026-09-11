"""Jost TypeInk factory. Builds section StylePacks — no role enum.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. ``JostRamp.packs()`` stamps a
frozen pack per section from the Jost catalog. Painters never call this;
they receive the pack from ``PlannerLayout``.

``family`` stays on the ink so a later dual-font factory can pick another
catalog family without ripping out the plotter kwarg. Today every field
resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost factory. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, weight: TypeWeight, size: float) -> TypeInk:
        """Stamp one Jost cut. Catalog raises if the weight has no file."""
        self.catalog.path("jost", weight)
        return TypeInk(family="jost", weight=weight, size=size)

    def packs(self):
        """Build the frozen per-section StylePacks from this catalog."""
        from parch.fonts.packs import PlannerPacks, build_jost_packs

        packs: PlannerPacks = build_jost_packs(self.catalog)
        return packs
