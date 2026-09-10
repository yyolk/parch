"""Meeting dest and week-banded index — data only. Painters seat the wells."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeetingAgenda:
    """Locked dest from #221. Index dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    agenda: int
    action_items: int
    index_dest: str = ""
    number: int = 0


@dataclass(frozen=True, slots=True)
class MeetingIndexRow:
    """One linked write-in under a week band."""

    dest: str


@dataclass(frozen=True, slots=True)
class MeetingIndexBand:
    """Week (or weekday) band — label is the scan header; rows hit dests."""

    label: str
    rows: tuple[MeetingIndexRow, ...]
    dated: bool = False


@dataclass(frozen=True, slots=True)
class MeetingIndex:
    """Thesis C — week-banded meeting index. Bands partition the page; rows link."""

    year: int
    dest: str
    bands: tuple[MeetingIndexBand, ...]
