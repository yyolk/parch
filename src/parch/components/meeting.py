"""Meeting index and dest — data only. Painters seat the roster and agenda."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeetingSlot:
    """One dense roster row — date cue + title write-in, linked to a Meeting dest."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class MeetingIndex:
    """Thesis A — dense dated roster. Each row is a dest to that Meeting page."""

    year: int
    dest: str
    slots: tuple[MeetingSlot, ...]


@dataclass(frozen=True, slots=True)
class MeetingAgenda:
    """Locked Meeting dest (#221). Ticket dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    agenda: int
    action_items: int
    index_dest: str = ""
    number: int = 0
