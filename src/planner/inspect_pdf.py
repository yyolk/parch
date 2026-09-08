"""Tiny helper: dump page count, named dests, and a few link annotations."""

from __future__ import annotations

from collections import Counter
from pathlib import Path


def inspect(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    lines = [
        f"file: {path}",
        f"pages: {len(reader.pages)}",
        f"title: {reader.metadata.title if reader.metadata else ''}",
    ]
    dests = reader.named_destinations
    lines.append(f"named_destinations: {len(dests)}")
    for key in ("cover", "year", "quarters", "months", "weeks", "days", "month-01", "day-2026-01-01"):
        lines.append(f"  dest {key}: {'yes' if key in dests else 'no'}")

    annot_pages = 0
    links = 0
    dest_hits: Counter[str] = Counter()
    for i, page in enumerate(reader.pages, start=1):
        annots = page.get("/Annots") or []
        if annots:
            annot_pages += 1
        for annot in annots:
            obj = annot.get_object()
            if obj.get("/Subtype") != "/Link":
                continue
            links += 1
            dest = obj.get("/Dest")
            if dest is not None:
                dest_hits[str(dest)[:80]] += 1
    lines.append(f"pages_with_annots: {annot_pages}")
    lines.append(f"link_annots: {links}")
    lines.append("sample dest values:")
    for dest, n in dest_hits.most_common(8):
        lines.append(f"  {n}× {dest}")
    # Cover (page 1) should have few/no nav-bar links; year page should have many.
    cover_annots = reader.pages[0].get("/Annots") or []
    year_annots = reader.pages[1].get("/Annots") or [] if len(reader.pages) > 1 else []
    lines.append(f"cover_link_annots: {len(cover_annots)}")
    lines.append(f"year_page_link_annots: {len(year_annots)}")
    return "\n".join(lines)


def main() -> int:
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "artifacts/specimen-2026.pdf"
    if not Path(path).is_file():
        print(f"missing {path}", file=sys.stderr)
        return 1
    print(inspect(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
