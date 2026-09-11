"""Hourly schedule strip — data + typography contract."""

from dataclasses import dataclass

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class ScheduleTypoNeeds:
    label: TypeRole = "well_label"
    hour: TypeRole = "schedule_hour"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.label, self.hour)

    def resolve(self, ramp: TypeRamp) -> "ScheduleInk":
        return ScheduleInk(label=ramp.ink(self.label), hour=ramp.ink(self.hour))


@dataclass(frozen=True, slots=True)
class ScheduleInk:
    label: TypeInk
    hour: TypeInk


@dataclass(frozen=True, slots=True)
class Schedule:
    label: str
    hours: tuple[int, ...]

    def typography(self) -> ScheduleTypoNeeds:
        return ScheduleTypoNeeds()
