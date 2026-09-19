"""Pack ``examples/*.toml`` into ``parch-examples.zip`` for CI / Release."""

from __future__ import annotations

import argparse
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from parch import ConfigError

EXAMPLES_ZIP_NAME = "parch-examples.zip"
EXAMPLES_ARC_PREFIX = "examples"


def examples_dir(root: Path | None = None) -> Path:
    """Repo ``examples/`` under ``root`` (default: cwd)."""
    base = Path.cwd() if root is None else root
    path = base / "examples"
    if not path.is_dir():
        raise ConfigError(f"examples/ not found under {base}")
    return path


def example_tomls(root: Path | None = None) -> list[Path]:
    """Sorted top-level ``*.toml`` files in ``examples/``."""
    files = sorted(path for path in examples_dir(root).glob("*.toml") if path.is_file())
    if not files:
        raise ConfigError("no example TOMLs to zip")
    return files


def arcname_for(path: Path) -> str:
    """Zip member path: ``examples/<stem>.toml``."""
    return f"{EXAMPLES_ARC_PREFIX}/{path.name}"


def write_examples_zip(dest: Path, root: Path | None = None) -> Path:
    """Write ``parch-examples.zip`` (or ``dest``) from repo examples."""
    files = example_tomls(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, arcname=arcname_for(path))
    return dest


def starter_name(arcname: str) -> str | None:
    """Toml stem for a zip member, or None if it is not a starter."""
    path = Path(arcname)
    if path.suffix != ".toml":
        return None
    if path.name.startswith(".") or path.name.startswith("__"):
        return None
    return path.stem


def starters_from_zip(data: bytes) -> dict[str, bytes]:
    """Map starter stem → TOML bytes. Duplicate stems fail loudly."""
    if not data:
        raise ConfigError("examples zip is empty")
    try:
        archive = zipfile.ZipFile(BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ConfigError("examples zip is not a zip") from exc
    starters: dict[str, bytes] = {}
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = starter_name(info.filename)
            if name is None:
                continue
            if name in starters:
                raise ConfigError(f"duplicate starter {name!r} in examples zip")
            starters[name] = archive.read(info)
    if not starters:
        raise ConfigError("examples zip has no starter TOMLs")
    return starters


def main(argv: list[str] | None = None) -> int:
    """Write ``parch-examples.zip`` (``-o`` overrides the path)."""
    parser = argparse.ArgumentParser(
        prog="python -m parch.services.examples_zip",
        description="Pack examples/*.toml into parch-examples.zip.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=EXAMPLES_ZIP_NAME,
        help=f"Destination zip path (default: {EXAMPLES_ZIP_NAME}).",
    )
    args = parser.parse_args(argv)
    try:
        path = write_examples_zip(Path(args.output))
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
