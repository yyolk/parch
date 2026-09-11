"""Weekly strip — data + typography contract. Linked in-month days carry a dest."""

from dataclasses import dataclass
from datetime import date

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class WeekDayTypoNeeds:
    dow: TypeRole = "week_dow"
    day: TypeRole = "week_day"
    month: TypeRole = "week_month"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.dow, self.day, self.month)

    def resolve(self, ramp: TypeRamp) -> "WeekDayInk":
        return WeekDayInk(
            dow=ramp.ink(self.dow),
            day=ramp.ink(self.day),
            month=ramp.ink(self.month),
        )


@dataclass(frozen=True, slots=True)
class WeekDayInk:
    dow: TypeInk
    day: TypeInk
    month: TypeInk


@dataclass(frozen=True, slots=True)
class WeekDay:
    day: date
    weekday_label: str
    dest: str | None
    in_month: bool

    def typography(self) -> WeekDayTypoNeeds:
        return WeekDayTypoNeeds()


@dataclass(frozen=True, slots=True)
class WeekStrip:
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    days: tuple[WeekDay, ...]

    def typography(self) -> WeekDayTypoNeeds:
        return WeekDayTypoNeeds()
