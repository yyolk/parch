"""Meeting dest, ticket index, and per-ticket agenda pages — data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeetingAgenda:
    """Locked Meeting dest. Ticket dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    agenda: int
    action_items: int
    index_dest: str = ""
    number: int = 0


@dataclass(frozen=True, slots=True)
class MeetingTicket:
    """One stacked ticket on the index — stub number + Meeting dest."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class MeetingsIndex:
    """Thesis B — stacked tickets. Stub and preview link; write-in stays unlinkable."""

    year: int
    dest: str
    tickets: tuple[MeetingTicket, ...]
