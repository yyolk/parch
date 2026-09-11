"""Lined notes well — data + typography contract. Daily seat and daily_notes pages."""

from dataclasses import dataclass

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class NotesTypoNeeds:
    label: TypeRole = "well_label"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.label,)

    def resolve(self, ramp: TypeRamp) -> "NotesInk":
        return NotesInk(label=ramp.ink(self.label))


@dataclass(frozen=True, slots=True)
class NotesInk:
    label: TypeInk


@dataclass(frozen=True, slots=True)
class Notes:
    label: str

    def typography(self) -> NotesTypoNeeds:
        return NotesTypoNeeds()
