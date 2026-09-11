"""Daily priorities checklist — data + typography contract. Painters draw ticks."""

from dataclasses import dataclass

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class PrioritiesTypoNeeds:
    label: TypeRole = "well_label"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.label,)

    def resolve(self, ramp: TypeRamp) -> "PrioritiesInk":
        return PrioritiesInk(label=ramp.ink(self.label))


@dataclass(frozen=True, slots=True)
class PrioritiesInk:
    label: TypeInk


@dataclass(frozen=True, slots=True)
class Priorities:
    label: str
    rows: int

    def typography(self) -> PrioritiesTypoNeeds:
        return PrioritiesTypoNeeds()
