"""Projects board, ticket index, and per-ticket three-card pages — data + ink."""

from dataclasses import dataclass

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class ProjectTicketTypoNeeds:
    stub: TypeRole = "ticket_stub"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.stub,)

    def resolve(self, ramp: TypeRamp) -> "ProjectTicketInk":
        return ProjectTicketInk(stub=ramp.ink(self.stub))


@dataclass(frozen=True, slots=True)
class ProjectTicketInk:
    stub: TypeInk


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    """G three-card well. Ticket dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    cards: int
    tasks: int
    index_dest: str = ""
    number: int = 0


@dataclass(frozen=True, slots=True)
class ProjectTicket:
    """One stacked ticket on the index — stub number + three-card projects dest."""

    number: int
    dest: str

    def typography(self) -> ProjectTicketTypoNeeds:
        return ProjectTicketTypoNeeds()


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis L — stacked tickets. Stub and preview cards link; write-in stays unlinkable."""

    year: int
    dest: str
    tickets: tuple[ProjectTicket, ...]

    def typography(self) -> ProjectTicketTypoNeeds:
        return ProjectTicketTypoNeeds()
