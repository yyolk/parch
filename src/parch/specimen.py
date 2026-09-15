"""fpdf2 specimen catalog: press key pages to PNG, write a static HTML gallery.

Catalog devices are SuperNote Nomad and Kindle Scribe. No paper×hand
permutations. Layout is ``<workdir>/specimens/<device-id>/``.
Each page writes one PNG (``{stem}.png`` at ``PREVIEW_DPI``). The device
index shrinks thumbs with CSS; a checkbox+label toggles expand in place.
The product PDF is not part of the catalog.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from pathlib import Path

from parch import ConfigError
from parch.books.projects_notebook import ProjectsNotebook
from parch.books.year_planner import YearPlanner
from parch.devices import get_device, known_device_ids
from parch.sections.page import Page
from parch.sections.steno import StenoPadSection
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

# Engineering notebook — cover + duplex faces, not YearPlanner dests.
ENGINEERING_STEMS = ("engineering-cover", "engineering-front", "engineering-back")

# Projects notebook — cover + index (sibling book dests).
PROJECTS_STEMS = ("projects-cover", "projects-index")

# Pad-only Gregg sheet (steno_sheets=1).
STENO_STEMS = ("steno",)

GALLERY_STEMS = (*SAMPLE_STEMS, *ENGINEERING_STEMS, *PROJECTS_STEMS, *STENO_STEMS)


def gallery_groups(
    stems: Sequence[str] = SAMPLE_STEMS,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Section id, heading, and stems for one device gallery."""
    return (
        ("year-planner", "Year planner", tuple(stems)),
        ("engineering-notebook", "Engineering notebook", ENGINEERING_STEMS),
        ("projects-notebook", "Projects notebook", PROJECTS_STEMS),
        ("steno-pad", "Steno pad", STENO_STEMS),
    )


GALLERY_GROUPS = gallery_groups()

PREVIEW_DPI = 96


def catalog_dest(workdir: str | Path) -> Path:
    """Catalog root: ``<workdir>/specimens/``."""
    return Path(workdir) / "specimens"


def specimens_dest(workdir: str | Path, device_id: str) -> Path:
    """Per-device dir: ``<workdir>/specimens/<device-id>/``."""
    return catalog_dest(workdir) / device_id


def specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Slim January press for catalog pages — not the product year book."""
    device = get_device(device_id)
    return Spec(device=device.id, year=year, months=(1,), notes_pages=1)


def projects_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Projects notebook press for catalog cover + index."""
    return replace(
        specimen_spec(device_id, year=year),
        book="projects-notebook",
        title="Projects",
    )


def steno_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """One Gregg pad sheet for the catalog."""
    return replace(
        specimen_spec(device_id, year=year), steno_sheets=1, title="Steno pad"
    )


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


def projects_dests(spec: Spec) -> dict[str, str]:
    """Named dest for each projects-notebook catalog stem."""
    return {
        "projects-cover": spec.cover_dest,
        "projects-index": spec.projects_index_dest,
    }


def steno_dests(spec: Spec) -> dict[str, str]:
    """Named dest for the pad-only steno catalog stem."""
    return {"steno": spec.dest_for_steno_pad(1)}


def _page_numbers(
    pages: Sequence[Page], dests: dict[str, str], stems: Sequence[str]
) -> dict[str, int]:
    by_dest = {page.dest: index for index, page in enumerate(pages, start=1)}
    numbers: dict[str, int] = {}
    for stem in stems:
        dest = dests[stem]
        if dest not in by_dest:
            raise ConfigError(
                f"specimen dest {dest!r} for {stem!r} is not in the press"
            )
        numbers[stem] = by_dest[dest]
    return numbers


def sample_page_numbers(
    spec: Spec, stems: Sequence[str] = SAMPLE_STEMS
) -> dict[str, int]:
    """1-based page numbers for requested stems, from the year-planner walk."""
    return _page_numbers(YearPlanner().pages(spec), sample_dests(spec), stems)


def projects_page_numbers(
    spec: Spec, stems: Sequence[str] = PROJECTS_STEMS
) -> dict[str, int]:
    """1-based page numbers from the projects-notebook walk."""
    return _page_numbers(ProjectsNotebook().pages(spec), projects_dests(spec), stems)


def steno_page_numbers(
    spec: Spec, stems: Sequence[str] = STENO_STEMS
) -> dict[str, int]:
    """1-based page numbers from the pad-only steno walk."""
    return _page_numbers(StenoPadSection(spec).pages(), steno_dests(spec), stems)


def _catalog_style() -> str:
    return (
        "<style>figure{display:inline-block;margin:1rem;vertical-align:top}"
        "figure>input{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}"
        "figure>label{display:block;cursor:zoom-in}"
        "figure>label img{width:16rem;height:auto;vertical-align:top}"
        "figure>input:checked+label{cursor:zoom-out}"
        "figure>input:checked+label img{width:auto;max-width:100%}</style>\n"
    )


def _figures(stems: Sequence[str]) -> list[str]:
    return [
        f'<figure><input type="checkbox" id="{stem}">'
        f'<label for="{stem}"><img src="{stem}.png" alt="{stem}"></label>'
        f"<figcaption>{stem}</figcaption></figure>"
        for stem in stems
    ]


def specimen_index_html(
    device_id: str,
    stems: Sequence[str] | None = None,
    *,
    groups: Sequence[tuple[str, str, Sequence[str]]] | None = None,
) -> str:
    """Device gallery: grouped sections, jump list, in-place expand."""
    if groups is None:
        groups = gallery_groups(SAMPLE_STEMS if stems is None else stems)
    toc = "\n".join(
        f'<li><a href="#{section_id}">{title}</a></li>'
        for section_id, title, _ in groups
    )
    sections = []
    for section_id, title, section_stems in groups:
        sections.append(
            f'<section id="{section_id}">\n'
            f"<h2>{title}</h2>\n" + "\n".join(_figures(section_stems)) + "\n</section>"
        )
    return (
        "<!DOCTYPE html>\n"
        f"<title>parch specimens — {device_id}</title>\n"
        + _catalog_style()
        + '<p><a href="../">specimens</a></p>\n'
        + "<nav>\n<ul>\n"
        + toc
        + "\n</ul>\n</nav>\n"
        + "\n".join(sections)
        + "\n"
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
    stems: Sequence[str] | None = None,
    groups: Sequence[tuple[str, str, Sequence[str]]] | None = None,
) -> Path:
    """Write the per-device index.html gallery."""
    dest.mkdir(parents=True, exist_ok=True)
    index = dest / "index.html"
    index.write_text(
        specimen_index_html(device_id, stems, groups=groups), encoding="utf-8"
    )
    return index


def _pdftoppm() -> str:
    path = shutil.which("pdftoppm")
    if path is None:
        raise ConfigError("pdftoppm not found (install poppler-utils)")
    return path


def render_page_png(
    pdf: Path, page: int, dest: Path, *, dpi: int = PREVIEW_DPI
) -> Path:
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


def _render_stems(
    pdf: Path, dest: Path, numbers: dict[str, int], stems: Sequence[str]
) -> None:
    for stem in stems:
        render_page_png(pdf, numbers[stem], dest / f"{stem}.png")


def write_specimens(
    dest: Path,
    device_id: str,
    *,
    stems: Sequence[str] = SAMPLE_STEMS,
    year: int = 2026,
) -> Path:
    """Press slim planner, notebooks, and steno pad; write PNGs + index."""
    spec = specimen_spec(device_id, year=year)
    dest.mkdir(parents=True, exist_ok=True)
    numbers = sample_page_numbers(spec, stems)
    from parch.press import press

    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "specimen.pdf"
        press(spec, pdf, proof=True)
        _render_stems(pdf, dest, numbers, stems)
        notebook = Path(tmp) / "engineering-notebook.pdf"
        press(
            replace(
                spec,
                book="engineering-notebook",
                engineering_sheets=1,
                title="Engineering",
            ),
            notebook,
            proof=True,
        )
        render_page_png(notebook, 1, dest / "engineering-cover.png")
        render_page_png(notebook, 2, dest / "engineering-front.png")
        render_page_png(notebook, 3, dest / "engineering-back.png")
        projects_spec = projects_specimen_spec(device_id, year=year)
        projects_pdf = Path(tmp) / "projects-notebook.pdf"
        press(projects_spec, projects_pdf, proof=True)
        _render_stems(
            projects_pdf,
            dest,
            projects_page_numbers(projects_spec),
            PROJECTS_STEMS,
        )
        steno_spec = steno_specimen_spec(device_id, year=year)
        steno_pdf = Path(tmp) / "steno-pad.pdf"
        press(steno_spec, steno_pdf, proof=True)
        _render_stems(steno_pdf, dest, steno_page_numbers(steno_spec), STENO_STEMS)
    write_device_index(dest, spec.device, groups=gallery_groups(stems))
    return dest


def build_catalog(
    workdir: str | Path,
    device_ids: Sequence[str] | None = None,
) -> Path:
    """Press each catalog device; write root index listing them."""
    ids = tuple(
        dict.fromkeys(get_device(d).id for d in (device_ids or known_device_ids()))
    )
    for device_id in ids:
        write_specimens(specimens_dest(workdir, device_id), device_id)
    root = catalog_dest(workdir)
    write_catalog_index(root, ids)
    return root


def build_device_catalog(workdir: str | Path, device_id: str) -> Path:
    """CLI entry: ``parch specimen DEVICE -w workdir``."""
    canonical = get_device(device_id).id
    build_catalog(workdir, (canonical,))
    return specimens_dest(workdir, canonical)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch specimen",
        description="Press key MVP pages to a static PNG catalog (fpdf2).",
    )
    parser.add_argument(
        "device",
        nargs="?",
        default=None,
        help="Device id. Omit to press every catalog device.",
    )
    parser.add_argument(
        "-w",
        "--workdir",
        default="./out",
        help="Catalog root parent (default ./out → ./out/specimens/<device>/).",
    )
    args = parser.parse_args(argv)
    try:
        dest = (
            build_catalog(args.workdir)
            if args.device is None
            else build_device_catalog(args.workdir, args.device)
        )
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(dest)
    return 0
