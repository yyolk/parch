"""One total function from ``PageKind`` to frame, strip, outline, and ink."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, assert_never, cast, get_args

from parch.calendar import quarter_of, short_date_range
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    BujoIndex,
    BujoKey,
    Checkoff365,
    CollectionLeaf,
    CoverTitle,
    DotGridPad,
    EngineeringPad,
    FavoritesPage,
    FutureLogPage,
    HabitGrid,
    LinedPad,
    MeetingAgenda,
    MeetingIndex,
    MonthGrid,
    MonthlyCalendarList,
    MonthlyTaskWell,
    My100Page,
    Notes,
    Priorities,
    ProjectsBoard,
    ProjectsIndex,
    QuarterGrid,
    RapidLogPage,
    ReviewIndex,
    ReviewWeekPage,
    Schedule,
    StenoPad,
    TasksIndex,
    TasksWeekPage,
    WeekStrip,
)
from parch.devices.registry import Device
from parch.fonts.ramp import TypeRamp
from parch.geom import Rect
from parch.plotter.protocol import Plotter
from parch.sections.page import Page, PageKind

type OutlinePolicy = Literal["run", "each", "skip"]
type Frame = Literal["bleed", "chrome"]
type Ink = Callable[[Plotter, Device, Page, TypeRamp, Rect | None], None]
type Pin = Callable[[Page, dict[str, str]], None]


@dataclass(frozen=True, slots=True)
class HeaderOverlay:
    """Header meta, chip, and link dests. Empty chip text hides the chip."""

    meta: str = ""
    meta_dest: str | None = None
    chip: str = ""
    chip_dest: str | None = None


type OverlayFn = Callable[[Page], HeaderOverlay]


@dataclass(frozen=True, slots=True)
class KindPlan:
    """Closed behavior for one page kind. Call sites read fields; they do not match."""

    frame: Frame
    strip: str
    outline: OutlinePolicy
    ink: Ink
    overlay: OverlayFn
    pin: Pin


def page_kinds() -> tuple[PageKind, ...]:
    """``PageKind`` tags in alias order. ``get_args`` on the alias itself is empty in 3.14."""
    return cast(tuple[PageKind, ...], get_args(PageKind.__value__))


def kind_plan(kind: PageKind) -> KindPlan:
    """Total map. A missing ``PageKind`` arm fails typecheck at ``assert_never``."""
    global _CACHE
    if _CACHE is None:
        _CACHE = _bind()
    return _CACHE[kind]


_CACHE: dict[PageKind, KindPlan] | None = None


def _one[T](page: Page, typ: type[T]) -> T:
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")


def _pin(label: str) -> Pin:
    """Write this page's dest onto one strip chip."""

    def pin(page: Page, dests: dict[str, str]) -> None:
        dests[label] = page.dest

    return pin


def _nop(_page: Page, _dests: dict[str, str]) -> None:
    """Leave strip dests as nav parsing left them."""


def _bare(_page: Page) -> HeaderOverlay:
    return HeaderOverlay()


def _overlay_annual(page: Page) -> HeaderOverlay:
    return HeaderOverlay("Q1–Q4", _one(page, AnnualGrid).quarter_dest)


def _overlay_favorites(page: Page) -> HeaderOverlay:
    return HeaderOverlay(str(_one(page, FavoritesPage).year))


def _overlay_my_100(page: Page) -> HeaderOverlay:
    leaf = _one(page, My100Page)
    chip = f"{leaf.page:02d}" if leaf.pages > 1 else ""
    dest = leaf.index_dest if leaf.pages > 1 else None
    return HeaderOverlay(str(leaf.year), chip=chip, chip_dest=dest)


def _overlay_checkoff(page: Page) -> HeaderOverlay:
    return HeaderOverlay(str(_one(page, Checkoff365).year))


def _overlay_projects_index(page: Page) -> HeaderOverlay:
    return HeaderOverlay(str(_one(page, ProjectsIndex).year))


def _overlay_project(page: Page) -> HeaderOverlay:
    board = _one(page, ProjectsBoard)
    chip = f"{board.number:02d}" if board.number else ""
    return HeaderOverlay(str(board.year), chip=chip, chip_dest=board.index_dest or None)


def _overlay_meetings_index(page: Page) -> HeaderOverlay:
    return HeaderOverlay(str(_one(page, MeetingIndex).year))


def _overlay_meeting(page: Page) -> HeaderOverlay:
    agenda = _one(page, MeetingAgenda)
    chip = f"{agenda.number:02d}" if agenda.number else ""
    return HeaderOverlay(
        str(agenda.year), chip=chip, chip_dest=agenda.index_dest or None
    )


def _overlay_tasks_index(page: Page) -> HeaderOverlay:
    return HeaderOverlay(f"Q{_one(page, TasksIndex).quarter}")


def _overlay_task(page: Page) -> HeaderOverlay:
    week = _one(page, TasksWeekPage)
    return HeaderOverlay(
        str(week.year),
        chip=f"W{week.iso_week:02d}",
        chip_dest=week.index_dest or None,
    )


def _overlay_review_index(page: Page) -> HeaderOverlay:
    return HeaderOverlay(str(_one(page, ReviewIndex).year))


def _overlay_review(page: Page) -> HeaderOverlay:
    week = _one(page, ReviewWeekPage)
    return HeaderOverlay(
        str(week.year),
        chip=f"W{week.iso_week:02d}",
        chip_dest=week.index_dest or None,
    )


def _overlay_month(page: Page) -> HeaderOverlay:
    grid = _one(page, MonthGrid)
    return HeaderOverlay(f"Q{quarter_of(grid.month)}", grid.quarter_dest)


def _overlay_habits(page: Page) -> HeaderOverlay:
    grid = _one(page, HabitGrid)
    meta = f"Q{quarter_of(grid.month)}" if grid.quarter_dest else ""
    return HeaderOverlay(meta, grid.quarter_dest)


def _overlay_weekly(page: Page) -> HeaderOverlay:
    week = _one(page, WeekStrip)
    return HeaderOverlay(short_date_range(week.monday, week.sunday))


def _overlay_daily(page: Page) -> HeaderOverlay:
    return HeaderOverlay(page.dest[:4])


def _overlay_daily_notes(page: Page) -> HeaderOverlay:
    label = _one(page, Notes).label
    meta = label.rsplit(" ", 1)[-1] if " " in label else page.dest[:4]
    return HeaderOverlay(meta)


def _overlay_bujo_key(page: Page) -> HeaderOverlay:
    return HeaderOverlay(page.dest.rsplit("-", 1)[-1])


def _overlay_bujo_index(page: Page) -> HeaderOverlay:
    index = _one(page, BujoIndex)
    return HeaderOverlay(f"{index.page}/{index.pages}")


def _overlay_future(page: Page) -> HeaderOverlay:
    future = _one(page, FutureLogPage)
    return HeaderOverlay(f"{future.page}/{future.pages}")


def _overlay_monthly_log(page: Page) -> HeaderOverlay:
    return HeaderOverlay("Tasks", _one(page, MonthlyCalendarList).tasks_dest)


def _overlay_monthly_tasks(page: Page) -> HeaderOverlay:
    tasks = _one(page, MonthlyTaskWell)
    return HeaderOverlay(tasks.month_name[:3], tasks.calendar_dest)


def _overlay_rapid(page: Page) -> HeaderOverlay:
    return HeaderOverlay(page.dest[:4])


def _overlay_collection(page: Page) -> HeaderOverlay:
    leaf = _one(page, CollectionLeaf)
    return HeaderOverlay(
        str(leaf.year),
        chip=f"{leaf.number:02d}",
        chip_dest=leaf.index_dest or None,
    )


def _pin_daily_notes(page: Page, dests: dict[str, str]) -> None:
    dests["Notes"] = page.dest
    dests["Day"] = page.dest.rsplit("-notes-", 1)[0]


def _pin_monthly_tasks(page: Page, dests: dict[str, str]) -> None:
    dests["Mon"] = dests.get("Mon", page.dest)


def _chrome(
    strip: str,
    outline: OutlinePolicy,
    ink: Ink,
    overlay: OverlayFn,
    pin: Pin,
) -> KindPlan:
    return KindPlan("chrome", strip, outline, ink, overlay, pin)


def _bleed(ink: Ink) -> KindPlan:
    return KindPlan("bleed", "", "skip", ink, _bare, _nop)


def _bind() -> dict[PageKind, KindPlan]:
    from parch.layouts.planner.painters import (
        paint_annual,
        paint_bujo_index,
        paint_bujo_key,
        paint_checkoff_365,
        paint_collection,
        paint_cover,
        paint_daily,
        paint_dotgrid_page,
        paint_engineering_pad,
        paint_favorites,
        paint_future_log,
        paint_habit_grid,
        paint_lined_page,
        paint_meeting,
        paint_meetings_index,
        paint_month_grid,
        paint_monthly_calendar_list,
        paint_monthly_task_well,
        paint_my_100,
        paint_notes,
        paint_project,
        paint_projects_index,
        paint_quarter,
        paint_rapid_log,
        paint_review,
        paint_review_index,
        paint_steno_pad,
        paint_task,
        paint_tasks_index,
        paint_week,
    )

    def ink_cover(
        plotter: Plotter,
        device: Device,
        page: Page,
        ramp: TypeRamp,
        _well: Rect | None,
    ) -> None:
        paint_cover(plotter, device, _one(page, CoverTitle), ramp=ramp)

    def ink_engineering(
        plotter: Plotter,
        device: Device,
        page: Page,
        ramp: TypeRamp,
        _well: Rect | None,
    ) -> None:
        paint_engineering_pad(plotter, device, _one(page, EngineeringPad), ramp=ramp)

    def ink_steno(
        plotter: Plotter,
        device: Device,
        page: Page,
        ramp: TypeRamp,
        _well: Rect | None,
    ) -> None:
        paint_steno_pad(plotter, device, _one(page, StenoPad), ramp=ramp)

    def ink_dotgrid(
        plotter: Plotter,
        device: Device,
        page: Page,
        ramp: TypeRamp,
        _well: Rect | None,
    ) -> None:
        paint_dotgrid_page(plotter, device, _one(page, DotGridPad), ramp=ramp)

    def ink_lined(
        plotter: Plotter,
        device: Device,
        page: Page,
        ramp: TypeRamp,
        _well: Rect | None,
    ) -> None:
        paint_lined_page(plotter, device, _one(page, LinedPad), ramp=ramp)

    def ink_annual(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_annual(plotter, well, _one(page, AnnualGrid), ramp=ramp)

    def ink_favorites(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_favorites(plotter, well, _one(page, FavoritesPage), ramp=ramp)

    def ink_my_100(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_my_100(plotter, well, _one(page, My100Page), ramp=ramp)

    def ink_checkoff(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_checkoff_365(plotter, well, _one(page, Checkoff365), ramp=ramp)

    def ink_projects_index(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_projects_index(plotter, well, _one(page, ProjectsIndex), ramp=ramp)

    def ink_project(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_project(plotter, well, _one(page, ProjectsBoard), ramp=ramp)

    def ink_meetings_index(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_meetings_index(plotter, well, _one(page, MeetingIndex), ramp=ramp)

    def ink_meeting(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_meeting(plotter, well, _one(page, MeetingAgenda), ramp=ramp)

    def ink_tasks_index(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_tasks_index(plotter, well, _one(page, TasksIndex), ramp=ramp)

    def ink_task(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_task(plotter, well, _one(page, TasksWeekPage), ramp=ramp)

    def ink_review_index(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_review_index(plotter, well, _one(page, ReviewIndex), ramp=ramp)

    def ink_review(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_review(plotter, well, _one(page, ReviewWeekPage), ramp=ramp)

    def ink_quarter(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_quarter(plotter, well, _one(page, QuarterGrid), ramp=ramp)

    def ink_month(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_month_grid(plotter, well, _one(page, MonthGrid), ramp=ramp)

    def ink_habits(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_habit_grid(plotter, well, _one(page, HabitGrid), ramp=ramp)

    def ink_week(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_week(plotter, well, _one(page, WeekStrip), ramp=ramp)

    def ink_daily(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_daily(
            plotter,
            well,
            _one(page, Schedule),
            _one(page, AnnualMonth),
            _one(page, Priorities),
            _one(page, Notes),
            ramp=ramp,
        )

    def ink_notes(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_notes(plotter, well, _one(page, Notes), ramp=ramp)

    def ink_bujo_key(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_bujo_key(plotter, well, _one(page, BujoKey), ramp=ramp)

    def ink_bujo_index(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_bujo_index(plotter, well, _one(page, BujoIndex), ramp=ramp)

    def ink_future(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_future_log(plotter, well, _one(page, FutureLogPage), ramp=ramp)

    def ink_monthly_log(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_monthly_calendar_list(
            plotter, well, _one(page, MonthlyCalendarList), ramp=ramp
        )

    def ink_monthly_tasks(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_monthly_task_well(plotter, well, _one(page, MonthlyTaskWell), ramp=ramp)

    def ink_rapid(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_rapid_log(plotter, well, _one(page, RapidLogPage), ramp=ramp)

    def ink_collection(
        plotter: Plotter,
        _device: Device,
        page: Page,
        ramp: TypeRamp,
        well: Rect | None,
    ) -> None:
        assert well is not None
        paint_collection(plotter, well, _one(page, CollectionLeaf), ramp=ramp)

    def plan(kind: PageKind) -> KindPlan:
        match kind:
            case "cover":
                return _bleed(ink_cover)
            case "engineering_front" | "engineering_back":
                return _bleed(ink_engineering)
            case "steno":
                return _bleed(ink_steno)
            case "dotgrid":
                return _bleed(ink_dotgrid)
            case "lined":
                return _bleed(ink_lined)
            case "annual":
                return _chrome("Year", "run", ink_annual, _overlay_annual, _pin("Year"))
            case "favorites":
                return _chrome(
                    "Fav", "run", ink_favorites, _overlay_favorites, _pin("Fav")
                )
            case "my_100":
                return _chrome("100", "run", ink_my_100, _overlay_my_100, _nop)
            case "checkoff_365":
                return _chrome(
                    "365", "run", ink_checkoff, _overlay_checkoff, _pin("365")
                )
            case "projects_index":
                return _chrome(
                    "Proj",
                    "run",
                    ink_projects_index,
                    _overlay_projects_index,
                    _pin("Proj"),
                )
            case "project":
                return _chrome("Proj", "skip", ink_project, _overlay_project, _nop)
            case "meetings_index":
                return _chrome(
                    "Meet",
                    "run",
                    ink_meetings_index,
                    _overlay_meetings_index,
                    _pin("Meet"),
                )
            case "meeting":
                return _chrome("Meet", "skip", ink_meeting, _overlay_meeting, _nop)
            case "tasks_index":
                return _chrome(
                    "Task", "run", ink_tasks_index, _overlay_tasks_index, _pin("Task")
                )
            case "task":
                return _chrome("Task", "skip", ink_task, _overlay_task, _nop)
            case "review_index":
                return _chrome(
                    "Rev", "run", ink_review_index, _overlay_review_index, _pin("Rev")
                )
            case "review":
                return _chrome("Rev", "skip", ink_review, _overlay_review, _nop)
            case "quarter":
                return _chrome("Quar", "each", ink_quarter, _bare, _pin("Quar"))
            case "month":
                return _chrome("Mon", "each", ink_month, _overlay_month, _pin("Mon"))
            case "habits":
                return _chrome(
                    "Habit", "skip", ink_habits, _overlay_habits, _pin("Habit")
                )
            case "weekly":
                return _chrome("Week", "skip", ink_week, _overlay_weekly, _pin("Week"))
            case "daily":
                return _chrome("Day", "skip", ink_daily, _overlay_daily, _pin("Day"))
            case "daily_notes":
                return _chrome(
                    "Notes", "skip", ink_notes, _overlay_daily_notes, _pin_daily_notes
                )
            case "bujo_key":
                return _chrome(
                    "Key", "run", ink_bujo_key, _overlay_bujo_key, _pin("Key")
                )
            case "bujo_index":
                return _chrome(
                    "Idx", "run", ink_bujo_index, _overlay_bujo_index, _pin("Idx")
                )
            case "future_log":
                return _chrome("Fut", "run", ink_future, _overlay_future, _pin("Fut"))
            case "monthly_log":
                return _chrome(
                    "Mon", "each", ink_monthly_log, _overlay_monthly_log, _pin("Mon")
                )
            case "monthly_tasks":
                return _chrome(
                    "Mon",
                    "skip",
                    ink_monthly_tasks,
                    _overlay_monthly_tasks,
                    _pin_monthly_tasks,
                )
            case "rapid_log":
                return _chrome("Day", "skip", ink_rapid, _overlay_rapid, _pin("Day"))
            case "collection":
                return _chrome(
                    "Col", "run", ink_collection, _overlay_collection, _pin("Col")
                )
            case _:
                assert_never(kind)

    return {kind: plan(kind) for kind in page_kinds()}
