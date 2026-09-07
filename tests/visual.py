"""Raster helpers for design checks; safe to delete with the tests that import them."""

import shutil
import subprocess
from pathlib import Path

from PIL import Image


def raster_page(pdf: Path, page: int, dest: Path, dpi: int = 150) -> Path:
    """Raster one 1-based PDF page to *dest* as a PNG via pdftoppm."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm is None:
        raise FileNotFoundError(
            "pdftoppm not found; install poppler-utils (CI already does)"
        )
    prefix = dest.with_suffix("")
    result = subprocess.run(
        [
            pdftoppm,
            "-png",
            "-r",
            str(dpi),
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            str(pdf),
            str(prefix),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"pdftoppm failed (page {page}, dpi {dpi}): {detail}")
    written = prefix.with_suffix(".png")
    if written != dest:
        written.replace(dest)
    if not dest.is_file():
        raise RuntimeError(f"pdftoppm did not write {dest}")
    return dest


def full_width_bands(
    image: Path,
    *,
    x0_frac: float = 0.12,
    dark: int = 64,
    coverage: float = 0.62,
) -> list[tuple[int, int, int]]:
    """Return (y0, y1, thickness_px) for dark full-width rows, skipping the MOS strip."""
    with Image.open(image) as src:
        im = src.convert("L")
    width, height = im.size
    pixels = im.load()
    x0 = int(width * x0_frac)
    span = width - x0
    dark_rows: list[int] = []
    for y in range(height):
        n = sum(1 for x in range(x0, width) if pixels[x, y] <= dark)
        if n / span >= coverage:
            dark_rows.append(y)
    out: list[tuple[int, int, int]] = []
    i = 0
    while i < len(dark_rows):
        start = dark_rows[i]
        end = start
        i += 1
        while i < len(dark_rows) and dark_rows[i] == end + 1:
            end = dark_rows[i]
            i += 1
        out.append((start, end, end - start + 1))
    return out


def ink_bands(
    image: Path,
    x: int,
    *,
    dark: int = 64,
    window: int = 2,
    coverage: float = 0.6,
) -> list[tuple[int, int, int]]:
    """Return (y0, y1, thickness_px) for dark rows around column *x*."""
    with Image.open(image) as src:
        im = src.convert("L")
    width, height = im.size
    pixels = im.load()
    x0 = max(0, x - window)
    x1 = min(width, x + window + 1)
    span = x1 - x0
    dark_rows: list[int] = []
    for y in range(height):
        n = sum(1 for xx in range(x0, x1) if pixels[xx, y] <= dark)
        if span and n / span >= coverage:
            dark_rows.append(y)
    out: list[tuple[int, int, int]] = []
    i = 0
    while i < len(dark_rows):
        start = dark_rows[i]
        end = start
        i += 1
        while i < len(dark_rows) and dark_rows[i] == end + 1:
            end = dark_rows[i]
            i += 1
        out.append((start, end, end - start + 1))
    return out


def card_interior_lines(
    image: Path,
    x: int,
    *,
    rows: int = 5,
    dark: int = 64,
) -> list[list[tuple[int, int, int]]]:
    """Each card is [top_frame, *3 interiors, bottom_frame] along column *x*."""
    thin = [b for b in ink_bands(image, x, dark=dark) if b[2] <= 2]
    cards: list[list[tuple[int, int, int]]] = []
    i = 0
    while i + 4 < len(thin):
        group = thin[i : i + 5]
        interiors = group[1:4]
        gap1 = interiors[1][0] - interiors[0][1]
        gap2 = interiors[2][0] - interiors[1][1]
        if abs(gap1 - gap2) <= 2 and min(gap1, gap2) >= 8:
            cards.append(group)
            i += 5
            continue
        i += 1
    if rows and len(cards) != rows:
        raise AssertionError(
            f"column x={x}: expected {rows} cards, got {len(cards)} from {thin}"
        )
    return cards


def header_first_ink_x(
    image: Path,
    *,
    skip_mm: float = 0,
    dpi: int = 150,
    dark: int = 100,
) -> int:
    """Leftmost ink x in the nav_header band, skipping *skip_mm* from the page edge."""
    return header_rail_adjacent_ink_x(
        image, rail="left", skip_mm=skip_mm, dpi=dpi, dark=dark
    )


def header_rail_adjacent_ink_x(
    image: Path,
    *,
    rail: str,
    skip_mm: float = 21.0,
    dpi: int = 150,
    dark: int = 100,
) -> int:
    """Ink x of the Contents chip, scanning inward from the MOS rail.

    Left rail: first ink after the rail. Right rail: last ink before the rail.
    """
    if rail not in {"left", "right"}:
        raise ValueError(f"rail must be left or right, got {rail!r}")
    from_right = rail == "right"
    bands = full_width_bands(
        image,
        x0_frac=0.0 if from_right else max(0.0, skip_mm / 157.5),
        coverage=0.45,
    )
    thin = [b for b in bands if b[2] <= 3]
    if not thin:
        raise AssertionError(f"no header rule in {image}")
    y1 = thin[0][0]
    y0 = max(0, int(dpi * 4 / 25.4))
    if y1 <= y0:
        raise AssertionError(f"header rule too high in {image}: {thin[0]}")
    with Image.open(image) as src:
        im = src.convert("L")
        width, _height = im.size
        pixels = im.load()
    skip = int(dpi * skip_mm / 25.4)
    if from_right:
        xs = range(width - 1 - skip, width // 2, -1)
    else:
        xs = range(skip, width // 2)
    for x in xs:
        if any(pixels[x, y] <= dark for y in range(y0, y1)):
            return x
    raise AssertionError(f"no header ink in {image}")


def ink_bbox(image: Path, *, dark: int = 64) -> tuple[int, int, int, int] | None:
    """Inclusive (x0, y0, x1, y1) of pixels darker than *dark*, or None."""
    with Image.open(image) as src:
        mask = src.convert("L").point(lambda p: 255 if p <= dark else 0)
    box = mask.getbbox()
    if box is None:
        return None
    x0, y0, x1, y1 = box
    return x0, y0, x1 - 1, y1 - 1
