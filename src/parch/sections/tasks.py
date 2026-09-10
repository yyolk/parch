from parch.calendar import month_touching_weeks
from parch.components import TaskTicket, TasksIndex, WeekTasks
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

TASK_ROWS = 8
TASK_CARRY = 3


class TasksSection:
    """Thesis B — ticket-stack Tasks index plus locked weekly dest pages."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        nav = planner_nav(spec, week_dest=week_dest)
        tickets = tuple(
            TaskTicket(number=slot, dest=spec.dest_for_task(slot))
            for slot in range(1, spec.task_count + 1)
        )
        per = spec.task_tickets
        built: list[Page] = []
        for page_i in range(1, spec.task_index_pages + 1):
            start = (page_i - 1) * per
            slice_tickets = tickets[start : start + per]
            dest = spec.dest_for_tasks_index(page_i)
            built.append(
                Page(
                    dest=dest,
                    kind="tasks_index",
                    title="Tasks",
                    nav=nav,
                    components=(
                        TasksIndex(
                            year=spec.year,
                            dest=dest,
                            tickets=slice_tickets,
                        ),
                    ),
                )
            )
        built.extend(
            Page(
                dest=ticket.dest,
                kind="task",
                title="Tasks",
                nav=planner_nav(
                    spec,
                    week_dest=week_dest,
                    task_dest=spec.dest_for_tasks_index_of(ticket.number),
                ),
                components=(
                    WeekTasks(
                        year=spec.year,
                        tasks=TASK_ROWS,
                        carry=TASK_CARRY,
                        index_dest=spec.dest_for_tasks_index_of(ticket.number),
                        number=ticket.number,
                    ),
                ),
            )
            for ticket in tickets
        )
        return built
