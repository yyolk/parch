# Spike notes (fpdf2 v2)

Written after generating a 2026 book in this environment. Visual craft first;
memory numbers land in [BENCH.md](BENCH.md) after the notes-pages matrix.

## Look (v2 vs v1 / ReportLab)

v1 (#204) was a working linked book with open hairline chrome. It read a bit
crude: thin header rule, active-tab wash only, unboxed mini-months, a short
boxed notes panel.

ReportLab (#205) used the same Helvetica-on-white product but tighter craft:
black header slab, inverted active nav tab on a washed strip, boxed mini-months,
open month rhythm (week gutter + row rules), two-column day, double-frame cover.
That was tuning, not Platypus.

This v2 rebuilds the fpdf2 canvas and aims at that #205 bar: one hairline
weight, one type hierarchy, full-bleed header/nav, boxed 6-row mini-months,
current-day invert, outlined chips. Still not parch chrome.

## Link model

Page-number links for taps (`add_link(page=N)` + `link()`). Named destinations
bound on each page (`set_link(name=…)` / `add_link(name=…)`) so `pypdf` can
resolve `day-2026-07-02`. `text()` y is a baseline; `link()` y is the top of
the box — helpers keep those apart.

## Layout

One `_mini_month` for year / quarter / day. Lined notes are a pitch loop.
You own every millimetre. Fine for a known 106 × 144 mm card; not a device
profile engine.
