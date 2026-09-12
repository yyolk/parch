"""Release PDF device matrix (device shards only)."""

import json
import subprocess
import sys

import pytest

from parch.devices import known_device_ids
from parch.services.release_pdfs import (
    PRESSABLE_DEVICE_IDS,
    matrix_json,
    matrix_shards,
    toml_for,
)


def test_pressable_shards_json():
    shards = matrix_shards()
    assert shards == [{"device": "supernote-nomad"}]
    assert json.loads(matrix_json()) == shards
    assert PRESSABLE_DEVICE_IDS == ("supernote-nomad",)


def test_pressable_is_not_registry():
    assert PRESSABLE_DEVICE_IDS != known_device_ids()
    assert "kindle-scribe" in known_device_ids()
    assert "kindle-scribe" not in PRESSABLE_DEVICE_IDS


def test_toml_for_pressable_nomad():
    assert toml_for("supernote-nomad") == "examples/mvp.toml"


def test_toml_for_rejects_unpressable():
    with pytest.raises(ValueError, match="is not pressable"):
        toml_for("kindle-scribe")
    with pytest.raises(ValueError, match="is not pressable"):
        toml_for("unknown-slate")


def test_module_prints_matrix_json():
    out = subprocess.check_output(
        [sys.executable, "-m", "parch.services.release_pdfs"],
        text=True,
    )
    assert json.loads(out) == matrix_shards()


def test_module_rejects_device_set_args():
    proc = subprocess.run(
        [sys.executable, "-m", "parch.services.release_pdfs", "hero"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "usage:" in proc.stderr
