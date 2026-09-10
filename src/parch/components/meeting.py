"""Meeting dest, index, and slots — data only. Painters seat them."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeetingAgenda:
    """Locked dest well — Title|Date, Agenda(4), Notes flex, Action items(3)."""

    year: int
    agenda: int
    action_items: int
    dest: str = ""
    index_dest: str = ""
    number: int = 0


@dataclass(frozen=True, slots=True)
class MeetingSlot:
    """One numbered dest on the index — stub + meeting dest."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class MeetingIndex:
    """Thesis E — featured next/focus dest + compact linked roster dests."""

    year: int
    dest: str
    featured: MeetingSlot
    entries: tuple[MeetingSlot, ...]
