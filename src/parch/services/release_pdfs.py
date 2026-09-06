"""Hero-device Release PDF matrix and lined paper overlay."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

from parch.services.job_file import emit_job, spec_from_data, with_overrides

HERO_DEVICE_IDS: tuple[str, ...] = (
    "supernote-nomad",
    "supernote-manta",
    "supernote-a5",
    "supernote-a5x",
    "supernote-a6",
    "supernote-a6x",
    "kindle-scribe",
    "kindle-scribe-11",
    "kindle-scribe-colorsoft",
    "remarkable-1",
    "remarkable-2",
)


def devices_json() -> str:
    """JSON array of hero device ids for the Release PDF matrix."""
    return json.dumps(list(HERO_DEVICE_IDS))


def set_job_paper(config_path: Path, paper: str) -> None:
    """Overlay style.scratch_pad on a live job file."""
    spec = spec_from_data(tomllib.loads(config_path.read_text(encoding="utf-8")))
    config_path.write_text(emit_job(with_overrides(spec, paper=paper)), encoding="utf-8")


def main() -> int:
    """Print hero device ids as a JSON array."""
    sys.stdout.write(devices_json() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
