"""Emit Spec defaults as plain TOML.

``parch init`` is the no-checkout, no-prompt path: values come from
``Spec()`` / ``from_mapping`` defaults, not from examples/ or questionary.
Guidance lives in the README.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from parch import ConfigError
from parch.spec import Spec


def starter_toml(spec: Spec | None = None) -> str:
    """Plain TOML of live Spec keys that round-trip through ``from_mapping``."""
    return (Spec() if spec is None else spec).to_toml()


def write_starter(path: Path, *, force: bool = False, spec: Spec | None = None) -> Path:
    """Write ``starter_toml`` to ``path``. Refuses to clobber unless ``force``."""
    if path.exists() and not force:
        raise ConfigError(f"{path} exists (pass --force to overwrite)")
    path.write_text(starter_toml(spec), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch init",
        description="Write Spec defaults as plain TOML (no prompts).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write starter TOML here. Default: stdout.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing --output file.",
    )
    args = parser.parse_args(argv)
    text = starter_toml()
    if args.output:
        try:
            dest = write_starter(Path(args.output), force=args.force)
        except ConfigError as exc:
            print(f"parch: {exc}", file=sys.stderr)
            return 2
        print(dest)
        return 0
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0
