"""Nomad year-month / mini-month dests: live days link; empty / omitted days stay none."""

from parch.mos.components.year_month import mini_month_cell, month_day_dests, year_month_cell
from parch.mos.manifest import Manifest
from tests.helpers import load_default, make_month


def test_month_day_dests_links_registered_days_only():
    manifest = Manifest()
    manifest.register_source("2026-01-01")
    manifest.register_source("2026-01-14")
    dests = month_day_dests(manifest, make_month("2026-01"))
    assert dests.startswith("(<2026-01-01>, ")
    assert ", <2026-01-14>, " in dests
    assert dests.count("<2026-01-") == 2
    assert dests.count("none") == 29


def test_year_month_cell_passes_day_dests():
    manifest = Manifest()
    manifest.register_source("month-2026-01-01")
    manifest.register_source("2026-01-01")
    cell = year_month_cell(load_default(), manifest, make_month("2026-01"))
    assert "year-month(" in cell
    assert "padded_link(<month-2026-01-01>)[January]" in cell
    assert "dests: (<2026-01-01>," in cell
    assert "none" in cell


def test_mini_month_cell_passes_day_dests():
    manifest = Manifest()
    manifest.register_source("2026-01-02")
    cell = mini_month_cell(load_default(), manifest, make_month("2026-01"), highlight=1)
    assert "mini-month(" in cell
    assert "highlight: 1" in cell
    assert "dests: (none, <2026-01-02>," in cell
