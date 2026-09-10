"""Meeting dest and mini-cover index — data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeetingAgenda:
    """Locked dest well (#221). Ticket dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    agenda: int
    action_items: int
    index_dest: str = ""
    number: int = 0


@dataclass(frozen=True, slots=True)
class MeetingCover:
    """One mini cover on the index — title rule + date cue, links to a dest."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class MeetingsIndex:
    """Thesis D — grid of mini covers. Whole cover links; write-ins stay blank."""

    year: int
    dest: str
    covers: tuple[MeetingCover, ...]
