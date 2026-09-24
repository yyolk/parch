"""fpdf2 specimen catalog: press key pages to PNG, write a static HTML gallery.

Catalog devices are SuperNote Nomad and Kindle Scribe. No paper×hand
permutations. Layout is ``<workdir>/specimens/<device-id>/``.
Each page writes one PNG (``{stem}.png`` at ``PREVIEW_DPI``). The device
index shrinks thumbs with CSS; a checkbox+label toggles expand in place.
The product PDF is not part of the catalog.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from pathlib import Path

from parch import ConfigError
from parch.books.bullet_journal import BulletJournal
from parch.books.dotgrid_notebook import DotGridNotebook
from parch.books.lined_dotgrid_notebook import LinedDotGridNotebook
from parch.books.lined_notebook import LinedNotebook
from parch.books.perspective_notebook import PerspectiveNotebook
from parch.books.projects_notebook import ProjectsNotebook
from parch.books.year_planner import YearPlanner
from parch.devices import get_device
from parch.dotgrid import dotgrid_pages
from parch.lined import lined_pages
from parch.perspective import perspective_pages
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

# Optional extras — Favorites, My 100, 365 Check-Off (nomad-extras.toml).
# Same year-planner press as SAMPLE_STEMS; own gallery heading.
EXTRAS_STEMS = ("favorites", "my-100", "checkoff-365")

# Engineering notebook — cover + duplex faces, not YearPlanner dests.
ENGINEERING_STEMS = ("engineering-cover", "engineering-front", "engineering-back")

# Projects notebook — cover + index + one project (sibling book dests).
PROJECTS_STEMS = ("projects-cover", "projects-index", "projects-project-1")

# Bullet journal — cover + key + index + future log (sibling dests; not the full walk).
BUJO_STEMS = ("bujo-cover", "bujo-key", "bujo-index", "bujo-future")

# Pad-only Gregg sheet (steno_sheets=1).
STENO_STEMS = ("steno",)

# Pad-only full-bleed clone-dot sheet (dotgrid_sheets=1).
DOTGRID_STEMS = ("dotgrid",)

# Pad-only full-bleed lined sheet (lined_sheets=1).
LINED_STEMS = ("lined",)

# Pad-only full-bleed perspective sheet (perspective_sheets=1).
PERSPECTIVE_STEMS = ("perspective",)

# Lined notebook — cover + one full-bleed lined page (sibling dests).
LINED_NOTEBOOK_STEMS = ("lined-cover", "lined-page")

# Lined / dotgrid notebook — cover + first lined + first dotgrid.
LINED_DOTGRID_NOTEBOOK_STEMS = (
    "lined-dotgrid-cover",
    "lined-dotgrid-lined",
    "lined-dotgrid-dotgrid",
)

# Dotgrid notebook — cover + one full-bleed clone-dot page (sibling dests).
DOTGRID_NOTEBOOK_STEMS = ("dotgrid-cover", "dotgrid-page")

# Perspective notebook — cover + one full-bleed perspective page.
PERSPECTIVE_NOTEBOOK_STEMS = ("perspective-cover", "perspective-page")

# Catalog Pages devices. Do not follow known_device_ids().
# Grow this tuple when a device should join gh-pages specimens.
CATALOG_DEVICE_IDS = ("supernote-nomad", "kindle-scribe")

DEFAULT_REPOSITORY = "yyolk/parch"


def gallery_groups(
    stems: Sequence[str] = SAMPLE_STEMS,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Section id, heading, and stems for one device gallery."""
    extras = frozenset(EXTRAS_STEMS)
    year = tuple(stem for stem in stems if stem not in extras)
    return (
        ("year-planner", "Year planner", year),
        ("optional-extras", "Optional extras", EXTRAS_STEMS),
        ("engineering-notebook", "Engineering notebook", ENGINEERING_STEMS),
        ("projects-notebook", "Projects notebook", PROJECTS_STEMS),
        ("bullet-journal", "Bullet Journal", BUJO_STEMS),
        ("dotgrid-notebook", "Dotgrid notebook", DOTGRID_NOTEBOOK_STEMS),
        ("lined-notebook", "Lined notebook", LINED_NOTEBOOK_STEMS),
        (
            "lined-dotgrid-mix-notebook",
            "Lined / dotgrid mix notebook",
            LINED_DOTGRID_NOTEBOOK_STEMS,
        ),
        ("perspective-notebook", "Perspective notebook", PERSPECTIVE_NOTEBOOK_STEMS),
        ("steno-pad", "Steno pad", STENO_STEMS),
        ("dotgrid-pad", "Dotgrid pad", DOTGRID_STEMS),
        ("lined-pad", "Lined pad", LINED_STEMS),
        ("perspective-pad", "Perspective pad", PERSPECTIVE_STEMS),
    )


GALLERY_GROUPS = gallery_groups()
GALLERY_STEMS = tuple(stem for _sid, _title, stems in GALLERY_GROUPS for stem in stems)

PREVIEW_DPI = 192


def catalog_dest(workdir: str | Path) -> Path:
    """Catalog root: ``<workdir>/specimens/``."""
    return Path(workdir) / "specimens"


def specimens_dest(workdir: str | Path, device_id: str) -> Path:
    """Per-device dir: ``<workdir>/specimens/<device-id>/``."""
    return catalog_dest(workdir) / device_id


def specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Slim January press for catalog pages — not the product year book."""
    device = get_device(device_id)
    return Spec(
        device=device.id,
        year=year,
        months=(1,),
        notes_pages=1,
    )


def projects_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Projects notebook press for catalog cover + index + one project."""
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


def dotgrid_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """One full-bleed clone-dot sheet for the catalog."""
    return replace(
        specimen_spec(device_id, year=year), dotgrid_sheets=1, title="Dot grid"
    )


def lined_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """One full-bleed lined sheet for the catalog."""
    return replace(
        specimen_spec(device_id, year=year), lined_sheets=1, title="Lined pad"
    )


def perspective_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """One full-bleed perspective sheet for the catalog."""
    return replace(
        specimen_spec(device_id, year=year),
        perspective_sheets=1,
        title="Perspective pad",
    )


def lined_notebook_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Lined notebook press for catalog cover + one lined page."""
    return replace(
        specimen_spec(device_id, year=year),
        book="lined-notebook",
        title="Lined",
        lined_sheets=1,
    )


def lined_dotgrid_notebook_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Lined / dotgrid notebook press for catalog cover + first pair."""
    return replace(
        specimen_spec(device_id, year=year),
        book="lined-dotgrid-mix-notebook",
        title="Lined / Dot grid",
        lined_dotgrid_sheets=1,
    )


def bujo_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Slim January bullet-journal press: one index page, one collection."""
    return replace(
        specimen_spec(device_id, year=year),
        book="bullet-journal",
        title="Bullet Journal",
        bujo_index_pages=1,
        bujo_collections=1,
    )


def perspective_notebook_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Perspective notebook press for catalog cover + one perspective page."""
    return replace(
        specimen_spec(device_id, year=year),
        book="perspective-notebook",
        title="Perspective",
        perspective_sheets=1,
    )


def dotgrid_notebook_specimen_spec(device_id: str, *, year: int = 2026) -> Spec:
    """Dotgrid notebook press for catalog cover + one clone-dot page."""
    return replace(
        specimen_spec(device_id, year=year),
        book="dotgrid-notebook",
        title="Dot grid",
        dotgrid_sheets=1,
    )


def sample_dests(spec: Spec) -> dict[str, str]:
    """Named dest for each catalog stem on *spec*."""
    jan1 = date(spec.year, 1, 1)
    return {
        "cover": spec.cover_dest,
        "annual": spec.year_dest,
        "favorites": spec.favorites_dest,
        "my-100": spec.my_100_dest,
        "checkoff-365": spec.checkoff_365_dest,
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
        "projects-project-1": spec.dest_for_project(1),
    }


def steno_dests(spec: Spec) -> dict[str, str]:
    """Named dest for the pad-only steno catalog stem."""
    return {"steno": spec.dest_for_steno_pad(1)}


def dotgrid_dests(spec: Spec) -> dict[str, str]:
    """Named dest for the pad-only dotgrid catalog stem."""
    return {"dotgrid": spec.dest_for_dotgrid_pad(1)}


def lined_dests(spec: Spec) -> dict[str, str]:
    """Named dest for the pad-only lined catalog stem."""
    return {"lined": spec.dest_for_lined_pad(1)}


def perspective_dests(spec: Spec) -> dict[str, str]:
    """Named dest for the pad-only perspective catalog stem."""
    return {"perspective": spec.dest_for_perspective_pad(1)}


def perspective_notebook_dests(spec: Spec) -> dict[str, str]:
    """Named dest for each perspective-notebook catalog stem."""
    return {
        "perspective-cover": spec.cover_dest,
        "perspective-page": spec.dest_for_perspective_pad(1),
    }


def lined_notebook_dests(spec: Spec) -> dict[str, str]:
    """Named dest for each lined-notebook catalog stem."""
    return {
        "lined-cover": spec.cover_dest,
        "lined-page": spec.dest_for_lined_pad(1),
    }


def lined_dotgrid_notebook_dests(spec: Spec) -> dict[str, str]:
    """Named dest for each lined-dotgrid-mix-notebook catalog stem."""
    return {
        "lined-dotgrid-cover": spec.cover_dest,
        "lined-dotgrid-lined": spec.dest_for_duplex_pair_pad(
            "lined-dotgrid", 1, "front"
        ),
        "lined-dotgrid-dotgrid": spec.dest_for_duplex_pair_pad(
            "lined-dotgrid", 1, "back"
        ),
    }


def bujo_dests(spec: Spec) -> dict[str, str]:
    """Named dest for each bullet-journal catalog stem."""
    return {
        "bujo-cover": spec.cover_dest,
        "bujo-key": spec.bujo_key_dest,
        "bujo-index": spec.bujo_index_dest,
        "bujo-future": spec.bujo_future_dest,
    }


def dotgrid_notebook_dests(spec: Spec) -> dict[str, str]:
    """Named dest for each dotgrid-notebook catalog stem."""
    return {
        "dotgrid-cover": spec.cover_dest,
        "dotgrid-page": spec.dest_for_dotgrid_pad(1),
    }


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


def dotgrid_page_numbers(
    spec: Spec, stems: Sequence[str] = DOTGRID_STEMS
) -> dict[str, int]:
    """1-based page numbers from the pad-only dotgrid walk."""
    return _page_numbers(dotgrid_pages(spec), dotgrid_dests(spec), stems)


def lined_page_numbers(
    spec: Spec, stems: Sequence[str] = LINED_STEMS
) -> dict[str, int]:
    """1-based page numbers from the pad-only lined walk."""
    return _page_numbers(lined_pages(spec), lined_dests(spec), stems)


def perspective_page_numbers(
    spec: Spec, stems: Sequence[str] = PERSPECTIVE_STEMS
) -> dict[str, int]:
    """1-based page numbers from the pad-only perspective walk."""
    return _page_numbers(perspective_pages(spec), perspective_dests(spec), stems)


def perspective_notebook_page_numbers(
    spec: Spec, stems: Sequence[str] = PERSPECTIVE_NOTEBOOK_STEMS
) -> dict[str, int]:
    """1-based page numbers from the perspective-notebook walk."""
    return _page_numbers(
        PerspectiveNotebook().pages(spec), perspective_notebook_dests(spec), stems
    )


def lined_notebook_page_numbers(
    spec: Spec, stems: Sequence[str] = LINED_NOTEBOOK_STEMS
) -> dict[str, int]:
    """1-based page numbers from the lined-notebook walk."""
    return _page_numbers(LinedNotebook().pages(spec), lined_notebook_dests(spec), stems)


def lined_dotgrid_notebook_page_numbers(
    spec: Spec, stems: Sequence[str] = LINED_DOTGRID_NOTEBOOK_STEMS
) -> dict[str, int]:
    """1-based page numbers from the lined-dotgrid-mix-notebook walk."""
    return _page_numbers(
        LinedDotGridNotebook().pages(spec),
        lined_dotgrid_notebook_dests(spec),
        stems,
    )


def bujo_page_numbers(spec: Spec, stems: Sequence[str] = BUJO_STEMS) -> dict[str, int]:
    """1-based page numbers from the bullet-journal walk."""
    return _page_numbers(BulletJournal().pages(spec), bujo_dests(spec), stems)


def dotgrid_notebook_page_numbers(
    spec: Spec, stems: Sequence[str] = DOTGRID_NOTEBOOK_STEMS
) -> dict[str, int]:
    """1-based page numbers from the dotgrid-notebook walk."""
    return _page_numbers(
        DotGridNotebook().pages(spec), dotgrid_notebook_dests(spec), stems
    )


def resolve_commit_sha(explicit: str | None = None) -> str | None:
    """Full SHA from *explicit*, ``GITHUB_SHA``, or ``git rev-parse HEAD``."""
    if explicit:
        return explicit.strip()
    env = os.environ.get("GITHUB_SHA", "").strip()
    if env:
        return env
    git = shutil.which("git")
    if git is None:
        return None
    try:
        completed = subprocess.run(
            [git, "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    except subprocess.CalledProcessError:
        return None
    return completed.stdout.strip() or None


def _commit_repository() -> str:
    return os.environ.get("GITHUB_REPOSITORY", "").strip() or DEFAULT_REPOSITORY


def _commit_footer(commit: str | None) -> str:
    if not commit:
        return ""
    sha = commit.strip()
    if not sha:
        return ""
    url = f"https://github.com/{_commit_repository()}/commit/{sha}"
    return f'<footer><a href="{url}">{sha[:7]}</a></footer>\n'


def _catalog_style() -> str:
    return (
        "<style>figure{display:inline-block;margin:1rem;vertical-align:top}"
        "figure>input{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}"
        "figure>label{display:block;cursor:zoom-in}"
        "figure>label img{width:16rem;height:auto;vertical-align:top}"
        "figure>input:checked+label{cursor:zoom-out}"
        "figure>input:checked+label img{width:auto;max-width:100%}"
        "footer{margin:2rem 1rem 1rem;font-size:0.85rem}</style>\n"
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
    commit: str | None = None,
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
        + '<header>\n<p><a href="../">specimens</a></p>\n</header>\n'
        + f"<h1>{device_id}</h1>\n"
        + "<nav>\n<ul>\n"
        + toc
        + "\n</ul>\n</nav>\n"
        + "\n".join(sections)
        + "\n"
        + _commit_footer(commit)
    )


def catalog_index_html(device_ids: Sequence[str], *, commit: str | None = None) -> str:
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
        + _commit_footer(commit)
    )


def write_catalog_index(
    root: Path, device_ids: Sequence[str], *, commit: str | None = None
) -> Path:
    """Write the catalog root index.html listing *device_ids*."""
    root.mkdir(parents=True, exist_ok=True)
    index = root / "index.html"
    index.write_text(
        catalog_index_html(device_ids, commit=resolve_commit_sha(commit)),
        encoding="utf-8",
    )
    return index


def write_device_index(
    dest: Path,
    device_id: str,
    *,
    stems: Sequence[str] | None = None,
    groups: Sequence[tuple[str, str, Sequence[str]]] | None = None,
    commit: str | None = None,
) -> Path:
    """Write the per-device index.html gallery."""
    dest.mkdir(parents=True, exist_ok=True)
    index = dest / "index.html"
    index.write_text(
        specimen_index_html(
            device_id,
            stems,
            groups=groups,
            commit=resolve_commit_sha(commit),
        ),
        encoding="utf-8",
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
    commit: str | None = None,
) -> Path:
    """Press slim planner, notebooks, pads; write PNGs + index."""
    spec = specimen_spec(device_id, year=year)
    dest.mkdir(parents=True, exist_ok=True)
    numbers = sample_page_numbers(spec, stems)
    extras = replace(spec, favorites_pages=1, my_100=True, checkoff_365=True)
    extras_numbers = sample_page_numbers(extras, EXTRAS_STEMS)
    from parch.press import press

    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "specimen.pdf"
        press(spec, pdf, proof=True)
        _render_stems(pdf, dest, numbers, stems)
        extras_pdf = Path(tmp) / "specimen-extras.pdf"
        press(extras, extras_pdf, proof=True)
        _render_stems(extras_pdf, dest, extras_numbers, EXTRAS_STEMS)
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
        bujo_spec = bujo_specimen_spec(device_id, year=year)
        bujo_pdf = Path(tmp) / "bullet-journal.pdf"
        press(bujo_spec, bujo_pdf, proof=True)
        _render_stems(bujo_pdf, dest, bujo_page_numbers(bujo_spec), BUJO_STEMS)
        notebook_spec = dotgrid_notebook_specimen_spec(device_id, year=year)
        notebook_pdf = Path(tmp) / "dotgrid-notebook.pdf"
        press(notebook_spec, notebook_pdf, proof=True)
        _render_stems(
            notebook_pdf,
            dest,
            dotgrid_notebook_page_numbers(notebook_spec),
            DOTGRID_NOTEBOOK_STEMS,
        )
        lined_notebook_spec = lined_notebook_specimen_spec(device_id, year=year)
        lined_notebook_pdf = Path(tmp) / "lined-notebook.pdf"
        press(lined_notebook_spec, lined_notebook_pdf, proof=True)
        _render_stems(
            lined_notebook_pdf,
            dest,
            lined_notebook_page_numbers(lined_notebook_spec),
            LINED_NOTEBOOK_STEMS,
        )
        pair_spec = lined_dotgrid_notebook_specimen_spec(device_id, year=year)
        pair_pdf = Path(tmp) / "lined-dotgrid-notebook.pdf"
        press(pair_spec, pair_pdf, proof=True)
        _render_stems(
            pair_pdf,
            dest,
            lined_dotgrid_notebook_page_numbers(pair_spec),
            LINED_DOTGRID_NOTEBOOK_STEMS,
        )
        steno_spec = steno_specimen_spec(device_id, year=year)
        steno_pdf = Path(tmp) / "steno-pad.pdf"
        press(steno_spec, steno_pdf, proof=True)
        _render_stems(steno_pdf, dest, steno_page_numbers(steno_spec), STENO_STEMS)
        dotgrid_spec = dotgrid_specimen_spec(device_id, year=year)
        dotgrid_pdf = Path(tmp) / "dotgrid-pad.pdf"
        press(dotgrid_spec, dotgrid_pdf, proof=True)
        _render_stems(
            dotgrid_pdf, dest, dotgrid_page_numbers(dotgrid_spec), DOTGRID_STEMS
        )
        lined_spec = lined_specimen_spec(device_id, year=year)
        lined_pdf = Path(tmp) / "lined-pad.pdf"
        press(lined_spec, lined_pdf, proof=True)
        _render_stems(lined_pdf, dest, lined_page_numbers(lined_spec), LINED_STEMS)
        perspective_notebook_spec = perspective_notebook_specimen_spec(
            device_id, year=year
        )
        perspective_notebook_pdf = Path(tmp) / "perspective-notebook.pdf"
        press(perspective_notebook_spec, perspective_notebook_pdf, proof=True)
        _render_stems(
            perspective_notebook_pdf,
            dest,
            perspective_notebook_page_numbers(perspective_notebook_spec),
            PERSPECTIVE_NOTEBOOK_STEMS,
        )
        perspective_spec = perspective_specimen_spec(device_id, year=year)
        perspective_pdf = Path(tmp) / "perspective-pad.pdf"
        press(perspective_spec, perspective_pdf, proof=True)
        _render_stems(
            perspective_pdf,
            dest,
            perspective_page_numbers(perspective_spec),
            PERSPECTIVE_STEMS,
        )
    write_device_index(dest, spec.device, groups=gallery_groups(stems), commit=commit)
    return dest


def build_catalog(
    workdir: str | Path,
    device_ids: Sequence[str] | None = None,
    *,
    commit: str | None = None,
) -> Path:
    """Press each catalog device; write root index listing them."""
    sha = resolve_commit_sha(commit)
    ids = tuple(
        dict.fromkeys(get_device(d).id for d in (device_ids or CATALOG_DEVICE_IDS))
    )
    for device_id in ids:
        write_specimens(specimens_dest(workdir, device_id), device_id, commit=sha)
    root = catalog_dest(workdir)
    write_catalog_index(root, ids, commit=sha)
    return root


def build_device_catalog(
    workdir: str | Path, device_id: str, *, commit: str | None = None
) -> Path:
    """CLI entry: ``parch specimen DEVICE -w workdir``."""
    canonical = get_device(device_id).id
    build_catalog(workdir, (canonical,), commit=commit)
    return specimens_dest(workdir, canonical)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch specimen",
        description="Press key pages to a static PNG catalog (fpdf2).",
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
    parser.add_argument(
        "--commit",
        default=None,
        help="Git SHA for the catalog footer (default: GITHUB_SHA or git HEAD).",
    )
    args = parser.parse_args(argv)
    try:
        dest = (
            build_catalog(args.workdir, commit=args.commit)
            if args.device is None
            else build_device_catalog(args.workdir, args.device, commit=args.commit)
        )
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(dest)
    return 0
