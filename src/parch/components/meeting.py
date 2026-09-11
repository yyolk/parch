"""Meeting index and dest — data only. Painters seat the roster and agenda."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeetingSlot:
    """One dense roster row — stub hits the Meeting dest; date/title write-ins stay unlinkable."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class MeetingIndex:
    """Dense dated roster for ``paint_meetings_index``. Stub per row is the dest hit; write-ins stay unlinkable."""

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
