# Spike notes (fpdf2 v2 vs v1 / ReportLab)

Written after generating a 2026 book in this environment.

## Look (v2 vs v1)

v1 (#204) was a working linked book. Chrome was an open hairline header, a
light wash only on the active nav tab, unboxed mini-months, and a short boxed
notes panel. It read a bit crude: inconsistent weights, loose type hierarchy,
calendar grids that floated.

ReportLab (#205) used the same Helvetica-on-white product but tighter craft:
double-frame cover, black header slab, inverted active tab on a washed strip,
boxed 6-row mini-months, open month rhythm (week gutter + row rules, no cell
cages), two-column day with current-day invert, more notes lines. That was
tuning, not Platypus.

This v2 rebuilds the fpdf2 canvas and aims at that #205 bar. Shared
`mini_month` / `text_box` / hairline helpers keep year, quarter, and day grids
on one rhythm. Header and nav are full-bleed. Notes are a pitch loop, not a
sparse framed well. Still not parch chrome — no MOS, no rail, no house style.

## Link model

fpdf2 has two useful layers:

1. **Integer page links** — `add_link(page=N)` / `link=`. The book is a fixed
   sequence, so every dest is a page number before the first `add_page`.
   Taps use this.
2. **Named destinations** (2.8.5+) — `set_link(name=…)` on the current page.
   Names (`day-2026-07-02`, `day-2026-07-02-notes-1`) show up in
   `pypdf.named_destinations` via the catalog Names/Dests tree.

`text()` y is a baseline; `link()` y is the top of the box (converted to PDF
space as `h_pt - y * k`). A `text_box` helper keeps labels optically centred
in header/nav/chips so those two conventions do not drift.

Do not pass `zoom="Fit"` into `add_link` / `set_link`. DestinationXYZ always
emits `/XYZ left top zoom`; a non-numeric zoom token (`Fit`) corrupts the
catalog.

## Memory / emit

A full 2026 book is **436 pages**, **436 named destinations**, and **~20k
link annotations**. Generation was about **1.2 seconds**. The PDF is **~3.1
MB** (Helvetica + strokes, no embedded fonts, no images). v2 is a little
fatter than v1 at N=0 (more calendar taps) and a little slimmer at N=100
(simpler notes chrome).

No intermediate `index.typst`. No subprocess. One Python process writes
bytes. ReportLab kept a larger in-memory graph (893 MiB vs 518 MiB at N=100)
and fatter files (~1.4×).

## Layout control

You own every millimetre. Mini-month cells are arithmetic (`width / 7`). Fine
for a known 106 × 144 mm card; miserable the moment you want device profiles
or “make this rail 8mm on Nomad”. Text wrapping and vertical rhythm are
manual. It looks like a planner and it is not a typesetting system.

## What hurt

- Helvetica core fonts are Latin-1. En-dash / em-dash blow up at emit
  (`FPDFUnicodeEncodingException`). ASCII hyphen only, unless you ship a
  Unicode font.
- Named dest + page link APIs are split across “Links” and “Named
  destinations”. Page links for taps; dest names as bookmarks-in-the-file.
- No free outline / tagged structure. `start_section` exists; this spike
  barely uses it.

## How links were checked

No GUI click-through. After `press`, `pypdf` was used to:

- Confirm dest page numbers (cover=1, year=2, Q1=3, January=7, first week=19,
  1 Jan=72, 31 Dec=436).
- Confirm the year-page nav strip is five bottom rectangles, and the cover
  has **no** nav annots (only the year numeral → year page).
- Confirm mid-year `day-2026-07-02` ↔ `…-notes-1` for every N≥2.

Pages were also rasterized with `pdftoppm` for the glanceable preview set.

## Notes-pages scale-up

See [BENCH.md](BENCH.md). Full-year 2026 was run at N = 0, 2, 10, 20, 30, 50,
100. Nothing OOM’d. N=100 was 36 936 pages / 26 s / **518 MiB** peak RSS.
Linear, not a notes-slab cliff. Slightly faster and leaner than fpdf2 v1;
clearly leaner than ReportLab on the same matrix.

## Verdict for the question

If the goal is **a working linked yearly PDF on one canvas**, fpdf2 is enough
and the second pass can look as tight as ReportLab without changing the
memory story. If the goal is **many devices, MOS/rail, Typst-quality type,
and a house style**, starting here still means re-inventing a layout engine
that Typst already is. This branch treats the planner as rectangles with
destinations. That is a valid product, just a different one.
