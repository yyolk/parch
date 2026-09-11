"""Explicit ``(family, weight) → TTF``. Constructed and passed — no ambient globals."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

type TypeFamily = Literal["jost", "besley", "martian"]
type TypeWeight = Literal["book", "medium", "bold", "heavy"]


def font_dir() -> Path:
    return Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class FontCatalog:
    """Curated cuts only. Missing pairs raise — do not invent a Heavy that has no file."""

    cuts: Mapping[tuple[str, str], Path]

    def path(self, family: str, weight: str) -> Path:
        try:
            return self.cuts[(family, weight)]
        except KeyError as exc:
            raise KeyError(f"no cut for family={family!r} weight={weight!r}") from exc

    def register_name(self, family: str, weight: str) -> str:
        self.path(family, weight)
        return f"{family}:{weight}"


def jost_catalog(root: Path | None = None) -> FontCatalog:
    """Jost Book / Medium / Bold / Heavy — the single-family ladder."""
    base = font_dir() if root is None else root
    return FontCatalog(
        {
            ("jost", "book"): base / "Jost-400-Book.ttf",
            ("jost", "medium"): base / "Jost-500-Medium.ttf",
            ("jost", "bold"): base / "Jost-700-Bold.ttf",
            ("jost", "heavy"): base / "Jost-800-Heavy.ttf",
        }
    )


def jost_besley_catalog(root: Path | None = None) -> FontCatalog:
    """Jost ladder plus Besley Regular (book) and Bold. No Besley medium/heavy files."""
    base = font_dir() if root is None else root
    return FontCatalog(
        {
            **jost_catalog(base).cuts,
            ("besley", "book"): base / "Besley-Regular.ttf",
            ("besley", "bold"): base / "Besley-Bold.ttf",
        }
    )


def martian_besley_catalog(root: Path | None = None) -> FontCatalog:
    """Jost + Besley plus Martian Regular (book) and Bold. No Martian medium/heavy files."""
    base = font_dir() if root is None else root
    return FontCatalog(
        {
            **jost_besley_catalog(base).cuts,
            ("martian", "book"): base / "martian-grotesk" / "MartianGrotesk-Regular.ttf",
            ("martian", "bold"): base / "martian-grotesk" / "MartianGrotesk-Bold.ttf",
        }
    )


# Alias: same three-family map. Unmigrated painters still need the Jost ladder.
jost_besley_martian_catalog = martian_besley_catalog
