"""Meeting page — data only. Painters seat the agenda."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeetingAgenda:
    year: int
    attendees: int
    agenda: int
    action_items: int
