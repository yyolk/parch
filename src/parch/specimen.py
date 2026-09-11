"""fpdf2 specimen catalog: press key pages to PNG, write a static HTML gallery.

Greenfield has one hero device (SuperNote Nomad) and no paper×hand
permutations. Catalog layout is ``<workdir>/specimens/<device-id>/``.
The product PDF is not part of the catalog.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from parch import ConfigError
from parch.books.year_planner import YearPlanner
from parch.devices import get_device, known_device_ids
from parch.spec import Spec

SAMPLE_STEMS = (
    "cover",
    "annual",
    "quarterly-q1",
    "monthly-jan",
    "weekly-w01",
    "daily-jan1",
    "notes-jan1",
    "projects",
    "project-1",
    "habits-jan",
    "review",
    "review-w01",
    "tasks",
    "tasks-w01",
    "meetings",
    "meeting-1",
)

PREVIEW_DPI = 96


def catalog_dest(workdir: str | Path) -> Path:
    """Catalog root: ``<workdir>/specimens/``."""
    return Path(workdir) / "specimens"


def specimens_dest(workdir: str | Path, device_id: str) -> Path:
    """Per-device dir: ``<workdir>/specimens/<device-id>/``."""
    return catalog_dest(workdir) / device_id


def listed_catalog_devices(root: Path) -> list[str]:
    """Device folders under the catalog root that have an index.html."""
    if not root.is_dir():
        return []
    found = {p.name for p in root.iterdir() if p.is_dir() and (p / "index.html").is_file()}
    known = known_device_ids()
    preferred = [device_id for device_id in known if device_id in found]
    extras = sorted(found - set(known))
    return preferred + extras


def specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Slim January press for catalog pages — not the product year book."""
    device = get_device(device_id)
    return Spec(device=device.id, year=year, months=(1,), notes_pages=1)


def sample_dests(spec: Spec) -> dict[str, str]:
    """Named dest for each catalog stem on *spec*."""
    jan1 = date(spec.year, 1, 1)
    return {
        "cover": spec.cover_dest,
        "annual": spec.year_dest,
        "quarterly-q1": spec.dest_for_quarter(1),
        "monthly-jan": spec.dest_for_month(1),
        "weekly-w01": spec.dest_for_week(jan1),
        "daily-jan1": spec.dest_for_day(jan1),
        "notes-jan1": spec.dest_for_notes(jan1, 1),
        "projects": spec.projects_index_dest,
        "project-1": spec.dest_for_project(1),
        "habits-jan": spec.dest_for_habits(1),
        "review": spec.review_index_dest,
        "review-w01": spec.dest_for_review(jan1),
        "tasks": spec.tasks_index_dest,
        "tasks-w01": spec.dest_for_task(jan1),
        "meetings": spec.meetings_index_dest,
        "meeting-1": spec.dest_for_meeting(1),
    }


def sample_page_numbers(spec: Spec, stems: Sequence[str] = SAMPLE_STEMS) -> dict[str, int]:
    """1-based page numbers for requested stems, from the year-planner walk."""
    dests = sample_dests(spec)
    by_dest = {page.dest: index for index, page in enumerate(YearPlanner().pages(spec), start=1)}
    numbers: dict[str, int] = {}
    for stem in stems:
        dest = dests[stem]
        if dest not in by_dest:
            raise ConfigError(f"specimen dest {dest!r} for {stem!r} is not in the press")
        numbers[stem] = by_dest[dest]
    return numbers


def _catalog_style() -> str:
    return (
        "<style>figure{display:inline-block;margin:1rem;vertical-align:top}"
        "img{width:16rem;height:auto}</style>\n"
    )


def specimen_index_html(device_id: str, stems: Sequence[str] = SAMPLE_STEMS) -> str:
    """Dumb device page: one gallery of PNG previews. No JS."""
    figures = [
        f'<figure><img src="{stem}.png" alt="{stem}">'
        f"<figcaption>{stem}</figcaption></figure>"
        for stem in stems
    ]
    return (
        "<!DOCTYPE html>\n"
        f"<title>parch specimens — {device_id}</title>\n"
        + _catalog_style()
        + '<p><a href="../">specimens</a></p>\n'
        + "<section>\n"
        + "\n".join(figures)
        + "</section>\n"
    )


def catalog_index_html(device_ids: Sequence[str]) -> str:
    """Dumb catalog root: device list. No galleries, no paper×hand tree."""
    items = "\n".join(
        f'<li><a href="{device_id}/">{device_id}</a></li>' for device_id in device_ids
    )
    return (
        "<!DOCTYPE html>\n"
        "<title>parch specimens</title>\n"
        + _catalog_style()
        + "<ul>\n"
        + items
        + "\n</ul>\n"
    )


def write_catalog_index(root: Path, device_ids: Sequence[str]) -> Path:
    """Write the catalog root index.html listing *device_ids*."""
    root.mkdir(parents=True, exist_ok=True)
    index = root / "index.html"
    index.write_text(catalog_index_html(device_ids), encoding="utf-8")
    return index


def write_device_index(
    dest: Path,
    device_id: str,
    *,
    stems: Sequence[str] = SAMPLE_STEMS,
) -> Path:
    """Write the per-device index.html gallery."""
    dest.mkdir(parents=True, exist_ok=True)
    index = dest / "index.html"
    index.write_text(specimen_index_html(device_id, stems), encoding="utf-8")
    return index


def _pdftoppm() -> str:
    path = shutil.which("pdftoppm")
    if path is None:
        raise ConfigError("pdftoppm not found (install poppler-utils)")
    return path


def render_page_png(pdf: Path, page: int, dest: Path, *, dpi: int = PREVIEW_DPI) -> Path:
    """Rasterize one 1-based PDF page to ``dest`` via pdftoppm."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    prefix = dest.with_suffix("")
    cmd = [
        _pdftoppm(),
        "-png",
        "-singlefile",
        "-f",
        str(page),
        "-l",
        str(page),
        "-r",
        str(dpi),
        str(pdf),
        str(prefix),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise ConfigError(f"pdftoppm failed: {detail or exc}") from exc
    if not dest.is_file() or dest.stat().st_size == 0:
        raise ConfigError(f"pdftoppm did not write {dest}")
    return dest


def write_specimens(
    dest: Path,
    device_id: str,
    *,
    stems: Sequence[str] = SAMPLE_STEMS,
    year: int = 2026,
) -> Path:
    """Press a slim book and write PNG previews + device index under *dest*."""
    spec = specimen_spec(device_id, year=year)
    dest.mkdir(parents=True, exist_ok=True)
    numbers = sample_page_numbers(spec, stems)
    from parch.press import press

    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "specimen.pdf"
        press(spec, pdf, proof=True)
        for stem in stems:
            render_page_png(pdf, numbers[stem], dest / f"{stem}.png")
    write_device_index(dest, spec.device, stems=stems)
    return dest


def build_device_catalog(workdir: str | Path, device_id: str) -> Path:
    """CLI entry: ``parch specimen DEVICE -w workdir``."""
    canonical = get_device(device_id).id
    dest = specimens_dest(workdir, canonical)
    write_specimens(dest, canonical)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch specimen",
        description="Press key MVP pages to a static PNG catalog (fpdf2).",
    )
    parser.add_argument(
        "device",
        nargs="?",
        default="supernote-nomad",
        help="Device id (default supernote-nomad).",
    )
    parser.add_argument(
        "-w",
        "--workdir",
        default="./out",
        help="Catalog root parent (default ./out → ./out/specimens/<device>/).",
    )
    args = parser.parse_args(argv)
    try:
        dest = build_device_catalog(args.workdir, args.device)
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(dest)
    return 0
