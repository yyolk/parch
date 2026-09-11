"""Press a spec to a PDF. CLI and ``python -m parch``."""

import argparse
import sys
from pathlib import Path

from parch import ConfigError
from parch.books.year_planner import YearPlanner
from parch.devices import get_device
from parch.fonts import JostBesleyRamp, JostRamp, TypeRamp
from parch.plotter.fpdf2 import Fpdf2Plotter
from parch.plotter.protocol import Plotter
from parch.spec import Spec

_DEVICE_TOKENS = {"supernote-nomad", "nomad"}
_RAMP_TOKENS = {"jost", "jost-besley"}


def _ramp_named(token: str) -> TypeRamp:
    match token:
        case "jost-besley":
            return JostBesleyRamp()
        case "jost":
            return JostRamp()
        case _:
            raise ConfigError(f"unknown ramp {token!r}; known: jost, jost-besley")


def press(
    spec: Spec,
    output: Path,
    plotter: Plotter | None = None,
    ramp: TypeRamp | None = None,
) -> Path:
    """Build the MVP book and write ``output``.

    Default ramp is ``JostRamp``. Pass ``JostBesleyRamp`` (or ``--ramp jost-besley``)
    for the dual-font specimen. The ramp's catalog is handed to ``Fpdf2Plotter``.
    """
    device = get_device(spec.device)
    resolved = JostRamp() if ramp is None else ramp
    if plotter is None:
        plotter = Fpdf2Plotter(device, catalog=resolved.catalog)
    YearPlanner(ramp=resolved).plot(spec, plotter)
    plotter.finish(output)
    return output


def _load_spec(token: str | None, *, year: int | None, month: int | None, day: int | None) -> Spec:
    match token:
        case None:
            spec = Spec()
        case device if device in _DEVICE_TOKENS:
            spec = Spec(device=device)
        case path_text if Path(path_text).is_file():
            spec = Spec.from_path(Path(path_text))
        case _:
            raise ConfigError(f"spec file not found: {token}")
    data = {
        "year": spec.year,
        "device": spec.device,
        "week_start": spec.week_start,
        "months": list(spec.months),
        "day": spec.day,
        "title": spec.title,
        "schedule_from": spec.schedule_from,
        "schedule_to": spec.schedule_to,
        "notes_pages": spec.notes_pages,
        "habit_columns": spec.habit_columns,
        "priority_rows": spec.priority_rows,
        "project_cards": spec.project_cards,
        "project_tasks": spec.project_tasks,
        "project_tickets": spec.project_tickets,
        "project_index_pages": spec.project_index_pages,
        "meeting_index_rows": spec.meeting_index_rows,
        "task_rows": spec.task_rows,
    }
    if year is not None:
        data["year"] = year
    if month is not None:
        data["months"] = [month]
    if day is not None:
        data["day"] = day
    return Spec.from_mapping(data)


def _outputs(args: argparse.Namespace, spec_token: str | None) -> list[Path]:
    paths: list[Path] = []
    if args.workdir:
        paths.append(Path(args.workdir) / "index.pdf")
    if args.output:
        paths.append(Path(args.output))
    if paths:
        return paths
    if spec_token and spec_token not in _DEVICE_TOKENS and Path(spec_token).is_file():
        return [Path(spec_token).with_suffix(".pdf")]
    return [Path("parch.pdf")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch",
        description="Press fixed e-ink PDF pages (greenfield MVP).",
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default=None,
        help="TOML spec path, or device id (supernote-nomad). Default: Nomad 2026 MVP.",
    )
    parser.add_argument("-o", "--output", help="Product PDF path.")
    parser.add_argument("-w", "--workdir", help="Also write workdir/index.pdf.")
    parser.add_argument("--year", type=int, help="Overlay planner year.")
    parser.add_argument("--month", type=int, help="MVP month (1–12).")
    parser.add_argument("--day", type=int, help="MVP daily page day-of-month.")
    parser.add_argument(
        "--ramp",
        choices=sorted(_RAMP_TOKENS),
        default="jost",
        help="Type ramp: jost (default) or jost-besley (dual-font specimen).",
    )
    # Accept a leading `press` verb so `parch press` and `python -m parch press` match.
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] == "press":
        raw = raw[1:]
    args = parser.parse_args(raw)
    try:
        spec = _load_spec(args.spec, year=args.year, month=args.month, day=args.day)
        outputs = _outputs(args, args.spec)
        first = press(spec, outputs[0], ramp=_ramp_named(args.ramp))
        for extra in outputs[1:]:
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_bytes(first.read_bytes())
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    for path in outputs:
        print(path)
    return 0
