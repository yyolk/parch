# Spike notes (ReportLab vs fpdf2 / Typst)

Written after generating a 2026 book in this environment.

## Layout choice

**Canvas, not Platypus.** Platypus wants a story of flowables and a frame.
These pages are a known 106 × 144 mm card: header slab, well, bottom tabs,
tap rectangles. `pdfgen.canvas` plus `bookmarkPage` / `linkAbsolute` is the
direct match. Destinations may be referenced before the page that binds them;
they must exist before `save()`.

Chrome is a black header + five equal footer tabs. Not MOS, not a rail, not
the fpdf2 spike’s drawing.

## Link model

ReportLab’s useful layer is **named destinations**:

1. `canvas.bookmarkPage(name, fit="Fit")` on each page (current page).
2. `canvas.linkAbsolute(contents, name, Rect=(x1,y1,x2,y2), Border='[0 0 0]')`.

`bookmarkPage` alone does **not** put names on the catalog. Links still work
(they hold an explicit `[pageRef /Fit]`), but `pypdf.named_destinations` is
empty. This spike publishes `canvas._destinations` as `Catalog.Dests` before
`save()` so the bench can count dests and resolve `day-2026-07-02`. pypdf
lists those keys with a leading slash.

Coordinates are **bottom-left origin**, default user space (points). Mini-month
cells are arithmetic (`width / 7`). Same tax as any canvas kit: you own every
millimetre; there is no measure/reflow.

Pain: y is a baseline for `drawString` and a corner for `rect` / `linkAbsolute`.
Easy to offset a tap if you mix the two. A small `_baseline()` helper keeps
header/tab labels optically centred.

## Memory / emit

A full 2026 book is **436 pages**, **436 named destinations**, and **~18k link
annotations**. ReportLab held it comfortably; generation was about **1.3
seconds**. The PDF is **~4.3 MB** (Helvetica + strokes, no embedded fonts, no
images). Annotation volume is the thing that would grow if every pixel of
chrome became a separate link.

No intermediate `index.typst`. No subprocess. The “press” is one Python
process writing bytes. ReportLab keeps the document graph until `save()`,
which shows up as higher RSS than fpdf2 once notes pages pile up (893 MiB vs
629 MiB at N=100) and as fatter files (~1.4×).

## Layout control

You own every millimetre. Year / quarter / day share one `_mini_month` so the
grids do not drift. Lined notes are a loop of `line()`. It looks like a
planner and it is not a typesetting system.

Device profiles, handed MOS, or “make this rail 8mm on Nomad” would mean
re-inventing the layout engine Typst already is.

## What hurt

- Helvetica only unless you ship font files. Fine for a spike; not i18n.
- Named dests are a two-step (bookmark + catalog `/Dests`). Docs talk about
  `bookmarkPage` / `linkAbsolute` / `linkRect`; they do not mention that
  `pypdf` will see nothing unless you emit `/Dests` or a name tree yourself.
- No free outline / tagged structure. `addOutlineEntry` exists; this spike
  does not use it.
- `linkRect` vs `linkAbsolute`: we stayed on `linkAbsolute` (default user
  space) so a later transform cannot silently move tap targets.

## How links were checked

No GUI click-through. After `press`, `pypdf` was used to:

- Confirm dest page numbers (cover=1, year=2, Q1=3, January=4 in the
  specimen; full book: first week=19, 1 Jan=72, 31 Dec=436).
- Confirm the year-page nav strip is five bottom rectangles, and the cover
  has **no** nav annots (only the year numeral → year page).
- Confirm mid-year `day-2026-07-02` ↔ `…-notes-1` for every N≥2.

Pages were also rasterized with `pdftoppm` for the glanceable preview set.

## Notes-pages scale-up

See [BENCH.md](BENCH.md). Full-year 2026 was run at N = 0, 2, 10, 20, 30, 50,
100. Nothing OOM’d. N=100 was 36 936 pages / 35 s / **893 MiB** peak RSS.
Linear, not a notes-slab cliff. Slightly slower and hungrier than fpdf2 on
the same matrix; same “just holds” verdict versus Typst.

## Verdict for the question

If the goal is **a working linked yearly PDF on one canvas**, open-source
ReportLab is enough and the code stays small. It is in the same performance
class as fpdf2: seconds, not a Typst compile; hundreds of MiB, not a notes
slab. If the goal is **many devices, MOS/rail, Typst-quality type, and a
house style**, starting here means re-inventing a layout engine that Typst
already is. This branch treats the planner as rectangles with destinations.
That is a valid product, just a different one.
