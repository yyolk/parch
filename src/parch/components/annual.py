"""Annual year grid — data + typography contract. Only pressed-month dests are set."""

from dataclasses import dataclass

from parch.components.month_grid import MonthWeek
from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class AnnualMonthTypoNeeds:
    name: TypeRole = "mini_month"
    name_on: TypeRole = "mini_month_on"
    dow: TypeRole = "mini_dow"
    day: TypeRole = "mini_day"
    day_on: TypeRole = "mini_day_on"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.name, self.name_on, self.dow, self.day, self.day_on)

    def resolve(self, ramp: TypeRamp) -> "AnnualMonthInk":
        return AnnualMonthInk(
            name=ramp.ink(self.name),
            name_on=ramp.ink(self.name_on),
            dow=ramp.ink(self.dow),
            day=ramp.ink(self.day),
            day_on=ramp.ink(self.day_on),
        )


@dataclass(frozen=True, slots=True)
class AnnualMonthInk:
    name: TypeInk
    name_on: TypeInk
    dow: TypeInk
    day: TypeInk
    day_on: TypeInk


@dataclass(frozen=True, slots=True)
class AnnualMonth:
    month: int
    name: str
    dest: str | None
    weekday_labels: tuple[str, ...]
    weeks: tuple[MonthWeek, ...]
    highlight_day: int | None = None

    def typography(self) -> AnnualMonthTypoNeeds:
        return AnnualMonthTypoNeeds()


@dataclass(frozen=True, slots=True)
class AnnualGrid:
    year: int
    months: tuple[AnnualMonth, ...]
    quarter_dest: str | None = None

    def typography(self) -> AnnualMonthTypoNeeds:
        return AnnualMonthTypoNeeds()
