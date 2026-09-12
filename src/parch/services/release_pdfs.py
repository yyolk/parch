"""Release PDF matrix: one shard per pressable device (no paper/hand matrix)."""

import json
import sys

# Release press is Nomad mvp.toml only. Do not follow known_device_ids().
# Grow this table (and PRESSABLE) when a device should ship a release PDF.
_PRESSABLE_TOML: dict[str, str] = {
    "supernote-nomad": "examples/mvp.toml",
}
PRESSABLE_DEVICE_IDS: tuple[str, ...] = tuple(_PRESSABLE_TOML)


def toml_for(device: str) -> str:
    """Spec path for a pressable device. Device must be in PRESSABLE and mapped."""
    try:
        return _PRESSABLE_TOML[device]
    except KeyError as exc:
        raise ValueError(f"device {device!r} is not pressable") from exc


def matrix_shards() -> list[dict[str, str]]:
    """One ``{device}`` shard per pressable id."""
    return [{"device": device} for device in PRESSABLE_DEVICE_IDS]


def matrix_json() -> str:
    """JSON array of ``{device}`` shards for the plan job."""
    return json.dumps(matrix_shards())


def main(argv: list[str] | None = None) -> int:
    """Print ``{device}`` shards as a JSON array."""
    args = sys.argv[1:] if argv is None else argv
    if args:
        raise SystemExit("usage: python -m parch.services.release_pdfs")
    sys.stdout.write(matrix_json() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
