"""Explicit ``(family, weight) → TTF``. Constructed and passed — no ambient globals."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

# Closed catalog key. Overlay accepts family= as a string so a later
# dual-font map can register more pairs without a TypePatch change.
# Widen this Literal when those files land — do not add Besley/Martian here.
type TypeFamily = Literal["jost"]
type TypeWeight = Literal["book", "medium", "bold", "heavy"]


def font_dir() -> Path:
    return Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class FontCatalog:
    """Curated cuts only. Missing pairs raise — do not invent a Heavy that has no file."""

    cuts: Mapping[tuple[str, str], Path]

    def path(self, family: str, weight: str) -> Path:
        """Resolve a cut. Unknown family or weight raises — do not invent files."""
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
