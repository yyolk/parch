"""Release PDF matrix: one shard per device (greenfield has no paper/hand)."""

import json
import sys

from parch.devices import known_device_ids

HERO_DEVICE_IDS: tuple[str, ...] = ("supernote-nomad",)


def device_ids(device_set: str = "hero") -> tuple[str, ...]:
    """Return hero or all known device ids."""
    if device_set == "hero":
        return HERO_DEVICE_IDS
    if device_set == "all":
        return known_device_ids()
    raise ValueError(f"unknown device_set {device_set!r}")


def matrix_shards(device_set: str = "hero") -> list[dict[str, str]]:
    """One ``{device}`` shard per id in the set."""
    return [{"device": device} for device in device_ids(device_set)]


def matrix_json(device_set: str = "hero") -> str:
    """JSON array of ``{device}`` shards for the plan job."""
    return json.dumps(matrix_shards(device_set))


def main(argv: list[str] | None = None) -> int:
    """Print ``{device}`` shards as a JSON array."""
    args = sys.argv[1:] if argv is None else argv
    device_set = args[0] if args else "hero"
    sys.stdout.write(matrix_json(device_set) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
