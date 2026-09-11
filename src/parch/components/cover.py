"""Cover title — data + typography contract."""

from dataclasses import dataclass

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class CoverTypoNeeds:
    year: TypeRole = "cover_year"
    brow: TypeRole = "cover_brow"
    spec: TypeRole = "cover_spec"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.year, self.brow, self.spec)

    def resolve(self, ramp: TypeRamp) -> "CoverInk":
        return CoverInk(
            year=ramp.ink(self.year),
            brow=ramp.ink(self.brow),
            spec=ramp.ink(self.spec),
        )


@dataclass(frozen=True, slots=True)
class CoverInk:
    year: TypeInk
    brow: TypeInk
    spec: TypeInk


@dataclass(frozen=True, slots=True)
class CoverTitle:
    year: int
    subtitle: str
    device_name: str
    cta_label: str
    cta_dest: str

    def typography(self) -> CoverTypoNeeds:
        return CoverTypoNeeds()
