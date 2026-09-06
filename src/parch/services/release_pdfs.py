"""Release PDF matrix: devices × paper × hand."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

from parch.devices import known_device_ids
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

HANDS: tuple[str, ...] = ("left", "right")
PAPERS: tuple[str, ...] = ("lined", "dotted")


def device_ids(device_set: str = "hero") -> tuple[str, ...]:
    """Return hero or all known device ids."""
    if device_set == "hero":
        return HERO_DEVICE_IDS
    if device_set == "all":
        return known_device_ids()
    raise ValueError(f"unknown device_set {device_set!r}")


def matrix_shards(device_set: str = "hero") -> list[dict[str, str]]:
    """Expand a device set across both papers and hands."""
    return [
        {"device": device, "hand": hand, "paper": paper}
        for device in device_ids(device_set)
        for paper in PAPERS
        for hand in HANDS
    ]


def matrix_json(device_set: str = "hero") -> str:
    """JSON array of {device, hand, paper} shards for the plan job."""
    return json.dumps(matrix_shards(device_set))


def assert_attach_allowed(
    device_set: str, event_name: str, release_tag: str = ""
) -> None:
    """Reject attaching the full catalog to a GitHub Release."""
    if device_set != "all":
        return
    if event_name == "release":
        raise ValueError("device_set=all is not allowed on release:published (hero only)")
    if release_tag:
        raise ValueError(
            f"device_set=all cannot attach to a Release (release_tag={release_tag}). "
            "Use empty release_tag for timing, or device_set=hero to upload."
        )


def devices_json(device_set: str = "hero") -> str:
    """JSON array of device ids for the chosen Release PDF set."""
    return json.dumps(list(device_ids(device_set)))


def set_job_paper(config_path: Path, paper: str) -> None:
    """Overlay style.scratch_pad on a live job file."""
    spec = spec_from_data(tomllib.loads(config_path.read_text(encoding="utf-8")))
    config_path.write_text(emit_job(with_overrides(spec, paper=paper)), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Print {device, hand, paper} shards as a JSON array."""
    args = sys.argv[1:] if argv is None else argv
    device_set = args[0] if args else "hero"
    sys.stdout.write(matrix_json(device_set) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
