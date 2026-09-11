"""Month grid — data + typography contract. Linked days carry a dest; others do not."""

from dataclasses import dataclass

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class MonthGridTypoNeeds:
    dow: TypeRole = "month_dow"
    week: TypeRole = "month_week"
    day: TypeRole = "month_day"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.dow, self.week, self.day)

    def resolve(self, ramp: TypeRamp) -> "MonthGridInk":
        return MonthGridInk(
            dow=ramp.ink(self.dow),
            week=ramp.ink(self.week),
            day=ramp.ink(self.day),
        )


@dataclass(frozen=True, slots=True)
class MonthGridInk:
    dow: TypeInk
    week: TypeInk
    day: TypeInk


@dataclass(frozen=True, slots=True)
class MonthCell:
    day: int | None
    dest: str | None = None
    in_month: bool = True


type MonthWeek = tuple[MonthCell, ...]


@dataclass(frozen=True, slots=True)
class MonthGrid:
    year: int
    month: int
    month_name: str
    weekday_labels: tuple[str, ...]
    weeks: tuple[MonthWeek, ...]
    week_dests: tuple[str, ...]
    quarter_dest: str | None = None
    habits_dest: str | None = None

    def typography(self) -> MonthGridTypoNeeds:
        return MonthGridTypoNeeds()
