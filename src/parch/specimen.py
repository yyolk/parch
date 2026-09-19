"""fpdf2 specimen catalog: press key pages to PNG, write a static HTML gallery.

Catalog devices are SuperNote Nomad and Kindle Scribe. No paper×hand
permutations. Layout is ``<workdir>/specimens/<device-id>/``.
Each page writes one PNG (``{stem}.png`` at ``PREVIEW_DPI``). The device
index shrinks thumbs with CSS; a checkbox+label toggles expand in place.
The product PDF is not part of the catalog.
"""

import argparse
import json
import os
import re
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
from parch.devices import get_device
from parch.sections.page import Page
from parch.sections.steno import StenoPadSection
from parch.spec import Spec

SAMPLE_STEMS = (
    "cover",
    "annual",
    "favorites",
    "my-100",
    "checkoff-365",
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

# Projects notebook — cover + index + one project (sibling book dests).
PROJECTS_STEMS = ("projects-cover", "projects-index", "projects-project-1")

# Pad-only Gregg sheet (steno_sheets=1).
STENO_STEMS = ("steno",)

# Catalog Pages devices. Do not follow known_device_ids().
# Grow this tuple when a device should join gh-pages specimens.
CATALOG_DEVICE_IDS = ("supernote-nomad", "kindle-scribe")

DEFAULT_REPOSITORY = "yyolk/parch"


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
GALLERY_STEMS = tuple(stem for _sid, _title, stems in GALLERY_GROUPS for stem in stems)

# Nearby catalog thumbs for the toml-preview spike. Same stem names on every
# catalog device; PNGs already live at ``../<device>/<stem>.png``.
PREVIEW_NEARBY = (
    ("year-planner", ("cover", "annual", "monthly-jan", "weekly-w01", "daily-jan1")),
    ("engineering-notebook", ENGINEERING_STEMS),
    ("projects-notebook", PROJECTS_STEMS),
    ("steno-pad", STENO_STEMS),
)

DEFAULT_PREVIEW_TOML = (
    "year = 2026\n"
    'device = "supernote-nomad"\n'
    'book = "year-planner"\n'
    "months = { from = 1, to = 12 }\n"
    "\n[daily]\n"
    "schedule = { from = 07:00:00, to = 16:00:00 }\n"
)

_PREVIEW_DEVICE_RE = re.compile(r'(?m)^\s*device\s*=\s*"([^"]+)"')
_PREVIEW_BOOK_RE = re.compile(r'(?m)^\s*book\s*=\s*"([^"]+)"')
_PREVIEW_ALIASES = {"nomad": "supernote-nomad", "scribe": "kindle-scribe"}

PREVIEW_DPI = 192


def specimen_preview_matrix(
    device_ids: Sequence[str] | None = None,
) -> dict[str, dict[str, list[str]]]:
    """Device → book → nearby catalog stems. Stand-in PNG lookup, not a press."""
    ids = tuple(device_ids or CATALOG_DEVICE_IDS)
    return {
        device_id: {book: list(stems) for book, stems in PREVIEW_NEARBY}
        for device_id in ids
    }


def preview_keys_from_toml(text: str) -> tuple[str, str]:
    """Spike scan: ``(device, book)`` from TOML text. Not ``tomllib``.

    ``book`` wins when present. Else ``[steno]`` / ``steno_sheets`` →
    ``steno-pad``, ``[engineering]`` / ``engineering_sheets`` →
    ``engineering-notebook``, else ``year-planner``. Device aliases
    (``nomad``, ``scribe``) canonicalize to catalog folder ids.
    """
    device_m = _PREVIEW_DEVICE_RE.search(text)
    device = device_m.group(1) if device_m else "supernote-nomad"
    device = _PREVIEW_ALIASES.get(device, device)
    book_m = _PREVIEW_BOOK_RE.search(text)
    if book_m:
        book = book_m.group(1)
    elif re.search(r"(?m)^\s*\[steno\]", text) or re.search(
        r"(?m)^\s*steno_sheets\s*=\s*[1-9]", text
    ):
        book = "steno-pad"
    elif re.search(r"(?m)^\s*\[engineering\]", text) or re.search(
        r"(?m)^\s*engineering_sheets\s*=\s*[1-9]", text
    ):
        book = "engineering-notebook"
    else:
        book = "year-planner"
    return device, book


def lookup_preview_stems(device_id: str, book: str = "year-planner") -> tuple[str, ...]:
    """Nearby catalog stems for *device_id* + *book*. Canonicalize aliases."""
    canonical = get_device(device_id).id
    row = specimen_preview_matrix().get(canonical)
    if row is None:
        raise ConfigError(f"unknown catalog device {canonical!r}")
    stems = row.get(book)
    if stems is None:
        raise ConfigError(f"unknown preview book {book!r}")
    return tuple(stems)


def preview_png_hrefs(device_id: str, book: str = "year-planner") -> tuple[str, ...]:
    """Relative hrefs from ``toml-preview/`` to existing catalog PNGs."""
    canonical = get_device(device_id).id
    return tuple(
        f"../{canonical}/{stem}.png" for stem in lookup_preview_stems(canonical, book)
    )


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
        favorites_pages=1,
        my_100=True,
        checkoff_365=True,
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
        + '<p><a href="../">specimens</a></p>\n'
        + "<nav>\n<ul>\n"
        + toc
        + "\n</ul>\n</nav>\n"
        + "\n".join(sections)
        + "\n"
        + _commit_footer(commit)
    )


def catalog_index_html(device_ids: Sequence[str], *, commit: str | None = None) -> str:
    """Dumb catalog root: device list + toml-preview spike. No galleries."""
    items = "\n".join(
        f'<li><a href="{device_id}/">{device_id}</a></li>' for device_id in device_ids
    )
    items += '\n<li><a href="toml-preview/">toml preview</a></li>'
    return (
        "<!DOCTYPE html>\n"
        "<title>parch specimens</title>\n"
        + _catalog_style()
        + "<ul>\n"
        + items
        + "\n</ul>\n"
        + _commit_footer(commit)
    )


def _preview_style() -> str:
    return (
        _catalog_style() + "<style>"
        "textarea{width:min(48rem,100%);min-height:16rem;font-family:monospace}"
        "#gallery figure{display:inline-block;margin:1rem;vertical-align:top}"
        "#gallery img{width:16rem;height:auto;vertical-align:top}"
        "#status{margin:1rem 0}"
        "</style>\n"
    )


def _preview_script() -> str:
    matrix = json.dumps(specimen_preview_matrix(), separators=(",", ":"))
    aliases = json.dumps(_PREVIEW_ALIASES, separators=(",", ":"))
    return (
        "<script>\n"
        f"var MATRIX={matrix};\n"
        f"var ALIAS={aliases};\n"
        "function keys(text){\n"
        '  var d=(text.match(/^\\s*device\\s*=\\s*"([^"]+)"/m)||[])[1]||\'supernote-nomad\';\n'
        "  d=ALIAS[d]||d;\n"
        '  var b=(text.match(/^\\s*book\\s*=\\s*"([^"]+)"/m)||[])[1];\n'
        "  if(!b){\n"
        "    if(/^\\s*\\[steno\\]/m.test(text)||/^\\s*steno_sheets\\s*=\\s*[1-9]/m.test(text)) b='steno-pad';\n"
        "    else if(/^\\s*\\[engineering\\]/m.test(text)||/^\\s*engineering_sheets\\s*=\\s*[1-9]/m.test(text)) b='engineering-notebook';\n"
        "    else b='year-planner';\n"
        "  }\n"
        "  return {device:d,book:b};\n"
        "}\n"
        "function stems(device,book,matrix){\n"
        "  var row=matrix[device]||{};\n"
        "  return row[book]||[];\n"
        "}\n"
        "function render(device,book,matrix){\n"
        "  var list=stems(device,book,matrix);\n"
        "  var g=document.getElementById('gallery');\n"
        "  var s=document.getElementById('status');\n"
        "  if(!matrix[device]){\n"
        "    g.innerHTML='';\n"
        "    s.textContent='unknown device '+device+' — catalog stems are supernote-nomad, kindle-scribe';\n"
        "    return;\n"
        "  }\n"
        "  if(!list.length){\n"
        "    g.innerHTML='';\n"
        "    s.textContent='no catalog stems for '+book+' on '+device;\n"
        "    return;\n"
        "  }\n"
        "  s.textContent='stand-in preview: '+device+' / '+book+' (matrix lookup, no press)';\n"
        "  g.innerHTML=list.map(function(stem){\n"
        "    var src='../'+device+'/'+stem+'.png';\n"
        "    return '<figure><img src=\"'+src+'\" alt=\"'+stem+'\"><figcaption>'+stem+'</figcaption></figure>';\n"
        "  }).join('');\n"
        "}\n"
        "function lookup(matrix){\n"
        "  var k=keys(document.getElementById('toml').value);\n"
        "  render(k.device,k.book,matrix||MATRIX);\n"
        "}\n"
        "function boot(matrix){\n"
        "  MATRIX=matrix||MATRIX;\n"
        "  var form=document.getElementById('preview');\n"
        "  form.addEventListener('submit',function(e){\n"
        "    e.preventDefault();\n"
        "    lookup(MATRIX);\n"
        "  });\n"
        "  document.getElementById('toml').addEventListener('input',function(){lookup(MATRIX)});\n"
        "  lookup(MATRIX);\n"
        "}\n"
        "fetch('matrix.json').then(function(r){return r.json()}).then(boot).catch(function(){boot(MATRIX)});\n"
        "</script>\n"
    )


def toml_preview_html() -> str:
    """Spike: editable Spec TOML + stand-in catalog PNGs. No press."""
    return (
        "<!DOCTYPE html>\n"
        "<title>parch spec preview</title>\n"
        + _preview_style()
        + '<p><a href="../">specimens</a></p>\n'
        "<h1>Spec TOML preview</h1>\n"
        "<p>Spike: edit TOML text. Submit POSTs to <code>preview</code> (intercepted) "
        "or runs a prebuilt specimen matrix lookup and shows nearby catalog PNGs "
        "keyed by device. Not a live press.</p>\n"
        '<form id="preview" method="post" action="preview">\n'
        '<p><label for="toml">toml</label></p>\n'
        f'<textarea id="toml" name="toml">{DEFAULT_PREVIEW_TOML}</textarea>\n'
        '<p><button type="submit">preview</button></p>\n'
        "</form>\n"
        '<p id="status"></p>\n'
        '<section id="gallery"></section>\n' + _preview_script()
    )


def write_toml_preview(root: Path) -> Path:
    """Write the catalog toml-preview spike page + matrix.json."""
    dest = root / "toml-preview"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "matrix.json").write_text(
        json.dumps(specimen_preview_matrix(), indent=2) + "\n",
        encoding="utf-8",
    )
    index = dest / "index.html"
    index.write_text(toml_preview_html(), encoding="utf-8")
    return index


def write_catalog_index(
    root: Path, device_ids: Sequence[str], *, commit: str | None = None
) -> Path:
    """Write the catalog root index.html listing *device_ids* plus toml-preview."""
    root.mkdir(parents=True, exist_ok=True)
    index = root / "index.html"
    index.write_text(
        catalog_index_html(device_ids, commit=resolve_commit_sha(commit)),
        encoding="utf-8",
    )
    write_toml_preview(root)
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
