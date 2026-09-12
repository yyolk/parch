"""Release PDF device matrix (device shards only)."""

import json
import subprocess
import sys

import pytest

from parch.devices import known_device_ids
from parch.services.release_pdfs import (
    HERO_DEVICE_IDS,
    device_ids,
    matrix_json,
    matrix_shards,
)


def test_hero_shards_json():
    hero = matrix_shards("hero")
    assert hero == [{"device": "supernote-nomad"}]
    assert json.loads(matrix_json("hero")) == hero
    assert device_ids() == HERO_DEVICE_IDS == ("supernote-nomad",)
    assert "kindle-scribe" not in HERO_DEVICE_IDS


def test_all_equals_known_device_ids():
    assert (
        device_ids("all") == known_device_ids() == ("supernote-nomad", "kindle-scribe")
    )


def test_device_ids_unknown_set_raises():
    with pytest.raises(ValueError, match="unknown device_set"):
        device_ids("unknown")


def test_module_prints_matrix_json():
    out = subprocess.check_output(
        [sys.executable, "-m", "parch.services.release_pdfs"],
        text=True,
    )
    assert json.loads(out) == matrix_shards("hero")
