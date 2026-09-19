"""Packaged starter TOMLs. ``examples/`` in the repo is the source of truth."""

from __future__ import annotations

import argparse
import sys
from importlib.resources import files
from pathlib import Path

from parch import ConfigError

DEFAULT_STARTER = "nomad"
STARTERS = frozenset({"nomad", "scribe"})
DEFAULT_PATH = Path("parch.toml")


def _checkout_example(name: str) -> Path | None:
    """Repo ``examples/`` when this module is loaded from a checkout."""
    for parent in Path(__file__).resolve().parents:
        if not (parent / "pyproject.toml").is_file():
            continue
        candidate = parent / "examples" / f"{name}.toml"
        if candidate.is_file():
            return candidate
    return None


def starter_bytes(name: str = DEFAULT_STARTER) -> bytes:
    """Read a packaged starter via ``importlib.resources``.

    After ``pip install``, hatchling force-includes ``examples/*.toml`` under
    this package. In a checkout / editable install the wheel mapping is
    absent, so fall back to repo ``examples/`` (the source of truth).
    """
    if name not in STARTERS:
        raise ConfigError(f"unknown starter {name!r}")
    resource = files(__package__).joinpath(f"{name}.toml")
    if resource.is_file():
        return resource.read_bytes()
    checkout = _checkout_example(name)
    if checkout is not None:
        return checkout.read_bytes()
    raise ConfigError(f"packaged starter missing: {name}.toml")


def write_starter(dest: Path, name: str = DEFAULT_STARTER) -> Path:
    """Copy one packaged starter to ``dest``. Refuses to overwrite."""
    dest = dest.expanduser()
    if dest.exists():
        raise ConfigError(f"refusing to overwrite {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(starter_bytes(name))
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch init",
        description=(
            "Write the packaged Nomad year planner TOML. "
            "Repo examples/ is the source of truth; the wheel ships a small snapshot."
        ),
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(DEFAULT_PATH),
        help="Destination path (default: parch.toml).",
    )
    args = parser.parse_args(argv)
    try:
        dest = write_starter(Path(args.path))
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(dest)
    return 0
