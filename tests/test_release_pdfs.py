"""Release PDF device matrix and attach guard (greenfield: device shards only)."""

import json
import subprocess
import sys

import pytest

from parch.devices import known_device_ids
from parch.services.release_pdfs import (
    HERO_DEVICE_IDS,
    MVP_SPEC,
    assert_attach_allowed,
    device_ids,
    devices_json,
    matrix_json,
    matrix_shards,
)


def test_hero_device_ids_are_canonical_and_unique():
    known = set(known_device_ids())
    assert HERO_DEVICE_IDS == ("supernote-nomad",)
    assert device_ids() == HERO_DEVICE_IDS
    assert device_ids("hero") == HERO_DEVICE_IDS
    assert len(HERO_DEVICE_IDS) == len(set(HERO_DEVICE_IDS))
    assert set(HERO_DEVICE_IDS) <= known


def test_device_ids_all_is_known_and_covers_hero():
    all_ids = device_ids("all")
    assert all_ids == known_device_ids()
    assert set(HERO_DEVICE_IDS) <= set(all_ids)
    assert "supernote-nomad" in all_ids
    assert "nomad" not in all_ids


def test_device_ids_unknown_set_raises():
    with pytest.raises(ValueError, match="unknown device_set"):
        device_ids("paper")


def test_assert_attach_allowed_blocks_all_on_release():
    assert_attach_allowed("hero", "release", "v0.3.0a0")
    assert_attach_allowed("hero", "workflow_dispatch", "v0.3.0a0")
    assert_attach_allowed("all", "workflow_dispatch", "")
    with pytest.raises(ValueError, match="hero only"):
        assert_attach_allowed("all", "release", "")
    with pytest.raises(ValueError, match="cannot attach"):
        assert_attach_allowed("all", "workflow_dispatch", "v0.3.0a0")


def test_devices_json_matches_hero_tuple():
    assert json.loads(devices_json()) == list(HERO_DEVICE_IDS)
    assert json.loads(devices_json("hero")) == list(HERO_DEVICE_IDS)
    assert json.loads(devices_json("all")) == list(known_device_ids())


def test_matrix_shards_are_device_only():
    hero = matrix_shards("hero")
    assert hero == [{"device": "supernote-nomad"}]
    assert matrix_shards("all") == [{"device": device} for device in known_device_ids()]
    assert json.loads(matrix_json("hero")) == hero
    for shard in hero:
        assert set(shard) == {"device"}
        assert "paper" not in shard
        assert "hand" not in shard
    names = [f"parch-0.3.0a0-{shard['device']}.pdf" for shard in hero]
    assert len(names) == len(set(names))
    assert MVP_SPEC == "examples/mvp.toml"


def test_module_prints_matrix_json():
    hero = subprocess.check_output(
        [sys.executable, "-m", "parch.services.release_pdfs"],
        text=True,
    )
    assert json.loads(hero) == matrix_shards("hero")
    explicit = subprocess.check_output(
        [sys.executable, "-m", "parch.services.release_pdfs", "hero"],
        text=True,
    )
    assert json.loads(explicit) == matrix_shards("hero")
    all_out = subprocess.check_output(
        [sys.executable, "-m", "parch.services.release_pdfs", "all"],
        text=True,
    )
    assert json.loads(all_out) == matrix_shards("all")
