"""Hero Release PDF device list and lined paper overlay."""

import json
import subprocess
import sys

import pytest

from parch.config import load
from parch.devices import known_device_ids
from parch.services.job_file import emit_job, spec_from_device
from parch.services.release_pdfs import (
    HERO_DEVICE_IDS,
    device_ids,
    devices_json,
    set_job_paper,
)

_EXCLUDED_FROM_HERO = (
    "158x210",
    "ipad-air-11",
    "ipad-mini",
    "ipad-pro-11",
    "ipad-pro-13",
    "remarkable-paper-pro",
    "remarkable-paper-pro-move",
    "remarkable-paper-pure",
)


def test_hero_device_ids_are_canonical_and_unique():
    known = set(known_device_ids())
    assert HERO_DEVICE_IDS == (
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
    assert device_ids() == HERO_DEVICE_IDS
    assert device_ids("hero") == HERO_DEVICE_IDS
    assert len(HERO_DEVICE_IDS) == len(set(HERO_DEVICE_IDS))
    assert set(HERO_DEVICE_IDS) <= known
    assert not set(_EXCLUDED_FROM_HERO) & set(HERO_DEVICE_IDS)


def test_device_ids_all_is_known_and_supersets_hero():
    all_ids = device_ids("all")
    assert all_ids == known_device_ids()
    assert len(all_ids) > len(HERO_DEVICE_IDS)
    assert set(HERO_DEVICE_IDS) <= set(all_ids)
    assert set(_EXCLUDED_FROM_HERO) <= set(all_ids)


def test_device_ids_unknown_set_raises():
    with pytest.raises(ValueError, match="unknown device_set"):
        device_ids("paper")


def test_devices_json_matches_hero_tuple():
    assert json.loads(devices_json()) == list(HERO_DEVICE_IDS)
    assert json.loads(devices_json("hero")) == list(HERO_DEVICE_IDS)
    assert json.loads(devices_json("all")) == list(known_device_ids())


def test_module_prints_devices_json():
    hero = subprocess.check_output(
        [sys.executable, "-m", "parch.services.release_pdfs"],
        text=True,
    )
    assert json.loads(hero) == list(HERO_DEVICE_IDS)
    explicit = subprocess.check_output(
        [sys.executable, "-m", "parch.services.release_pdfs", "hero"],
        text=True,
    )
    assert json.loads(explicit) == list(HERO_DEVICE_IDS)
    all_out = subprocess.check_output(
        [sys.executable, "-m", "parch.services.release_pdfs", "all"],
        text=True,
    )
    assert json.loads(all_out) == list(known_device_ids())


def test_set_job_paper_overlays_scratch_pad(tmp_path):
    path = tmp_path / "job.toml"
    path.write_text(emit_job(spec_from_device("supernote-nomad")), encoding="utf-8")
    assert load(path)["planner"]["params"]["scratch_pad"] == "dotted"
    set_job_paper(path, "lined")
    assert load(path)["planner"]["params"]["scratch_pad"] == "lined"
    assert load(path)["planner"]["params"]["mos_layout"]["side_menu_position"] == "left"
