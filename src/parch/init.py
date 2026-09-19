"""Write a baked-in profile TOML to cwd. Flags only; never prompts."""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

from parch import ConfigError
from parch.devices import get_device
from parch.spec import Spec

PROFILE_NAMES = ("nomad", "scribe", "bujo", "extras")

_YEAR_ASSIGN = re.compile(r"(?m)^[ \t]*year\s*=\s*\d+")
_DEVICE_ASSIGN = re.compile(r'(?m)^[ \t]*device\s*=\s*"[^"]*"')


def profile_dir() -> Path:
    """Package-data directory of baked-in starter TOMLs."""
    return Path(__file__).resolve().parent / "profiles"


def profile_text(name: str) -> str:
    """Return the baked-in TOML for ``name``. Unknown names raise ``ConfigError``."""
    if name not in PROFILE_NAMES:
        known = ", ".join(PROFILE_NAMES)
        raise ConfigError(f"unknown profile {name!r}; known profiles: {known}")
    path = profile_dir() / f"{name}.toml"
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"profile {name!r}: {exc}") from exc


def overlay_profile(
    text: str,
    *,
    year: int | None = None,
    device: str | None = None,
) -> str:
    """Surgically overlay ``year`` / ``device``; comments and neighbors stay put."""
    if year is not None:
        if not (
            isinstance(year, int) and not isinstance(year, bool) and 1 <= year <= 9999
        ):
            raise ConfigError("year must be between 1 and 9999")
        if not _YEAR_ASSIGN.search(text):
            raise ConfigError("profile has no year assignment to overlay")
        text = _YEAR_ASSIGN.sub(f"year = {year}", text, count=1)
    if device is not None:
        get_device(device)
        if not _DEVICE_ASSIGN.search(text):
            raise ConfigError("profile has no device assignment to overlay")
        text = _DEVICE_ASSIGN.sub(f'device = "{device}"', text, count=1)
    return text


def write_profile(dest: Path, text: str) -> Path:
    """Validate TOML via ``Spec.from_path``, then replace ``dest``. No overwrite."""
    if dest.exists():
        raise ConfigError(f"{dest} already exists")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp: Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(dir=dest.parent, suffix=".toml")
        tmp = Path(tmp_name)
        try:
            handle = os.fdopen(fd, "w", encoding="utf-8")
        except Exception:
            os.close(fd)
            raise
        with handle:
            handle.write(text)
        Spec.from_path(tmp)
        tmp.replace(dest)
    except OSError as exc:
        raise ConfigError(f"{dest}: {exc}") from exc
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return dest


def init_profile(
    name: str,
    *,
    year: int | None = None,
    device: str | None = None,
    cwd: Path | None = None,
) -> Path:
    """Write ``<name>.toml`` under ``cwd`` (default: process cwd). Never prompts."""
    root = Path.cwd() if cwd is None else cwd
    dest = root / f"{name}.toml"
    text = overlay_profile(profile_text(name), year=year, device=device)
    return write_profile(dest, text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch init",
        description=(
            "Write a baked-in profile TOML to the current directory. "
            "Flags only; never prompts."
        ),
    )
    parser.add_argument(
        "--profile",
        required=True,
        choices=PROFILE_NAMES,
        help="Starter TOML written to cwd as <profile>.toml.",
    )
    parser.add_argument("--year", type=int, help="Overlay planner year.")
    parser.add_argument(
        "--device",
        help="Overlay device id (supernote-nomad, nomad, kindle-scribe, scribe).",
    )
    args = parser.parse_args(argv)
    try:
        dest = init_profile(args.profile, year=args.year, device=args.device)
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(dest)
    return 0
