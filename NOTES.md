# Spike notes (ReportLab vs fpdf2 / Typst)

Written while the generator was standing up. Bench numbers land in
[BENCH.md](BENCH.md) after the notes-pages matrix.

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

Coordinates are **bottom-left origin**, default user space (points). Mini-month
cells are arithmetic (`width / 7`). Same tax as any canvas kit: you own every
millimetre; there is no measure/reflow.

pypdf should see `bookmarkPage` names in `named_destinations`. Link annots
are `/Subtype /Link` with a dest bound to that name. Counting method is
documented in BENCH.md after the first inspect.

## First impressions (pre-bench)

- Helvetica built-ins only. Fine for a spike; not i18n.
- Year / quarter / month share one `_mini_month` so the grids do not drift.
- Lined notes are a loop of `line()`. It looks like a planner, not a
  typesetting system.
- ReportLab keeps the document graph until `save()`. Memory vs fpdf2 is the
  question the notes-pages matrix is meant to answer.

## Verdict so far

Enough to glance at a specimen. Whether ReportLab holds at N=10…100 the way
fpdf2 did is the rest of this spike.
