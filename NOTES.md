# Spike notes (fpdf2 vs Typst path)

Written after generating a 2026 book in this environment. Honest and short.

## Link model

fpdf2 has two useful layers:

1. **Integer page links** — `add_link(page=N)` / `link=`. You can precompute every
   page number (the book is a fixed sequence) and stamp rectangles later. This is
   what the tap targets use. It is boring and it works.
2. **Named destinations** (2.8.5+) — `set_link(name=…)` to reserve,
   `add_link(name=…)` to bind the current page, `link="#name"` to jump. Good
   semantic handles (`day-2026-01-01`) and they survive if you reshuffle emit
   order, but you still have to remember to reserve before the first forward
   reference if you rely on `#name` alone.

Typst’s label / `link(<label>)` story is closer to named dests. MOS/rail code
in parch spends a lot of energy making hit targets line up with a layout
grid. Here a hit target is just a rectangle you draw yourself. No chase
geometry, no house.typ. That is the whole appeal.

Pain: `FPDF.link` y is the *top* of the box in user space, while `text()` y is
a baseline. Easy to offset a tap rect by a few millimetres if you mix the two.
`cell` + `link=` is safer for chrome; raw `link()` is better for calendar
cells.

## Memory / emit

A full 2026 book is **436 pages**, **440 named destinations**, and **~17k link
annotations**. fpdf2 held it comfortably in this VM; generation was about **2
seconds**, not a Typst compile. The PDF is **~2.6 MB** (Helvetica + strokes, no
embedded fonts, no images). Annotation volume is the thing that would grow if
every pixel of chrome became a separate link.

No intermediate `index.typst`. No subprocess. The “press” is one Python
process writing bytes. That part felt like the original LYP promise minus the
TeX.

## Layout control

You own every millimetre. That is also the tax: there is no show rule, no
grid that reflows, no `measure()`. Mini-month cells are arithmetic
(`width / 7`). Fine for a known page size; miserable the moment you want
device profiles, handed MOS, or “make this rail 8mm on Nomad and 0 on Scribe”.

Text wrapping and vertical rhythm are manual. Lined notes are a loop of
`line()`. It looks like a planner and it is not a typesetting system.

## What hurt

- Helvetica only unless you ship font files. Fine for a spike; not fine for
  i18n (explicit non-goal).
- No shared layout language, so year / quarter / month calendars drift unless
  you discipline yourself with one `draw_mini_month`.
- Named dests and page links both exist; docs are split across “Links” and
  “Named destinations”. I used page links for taps and dest names as
  bookmarks-in-the-file so a reader or a later merge can still say “go to
  `month-01`”.
- I did not get Typst’s free outline / PDF tagged structure. `start_section`
  exists in fpdf2; this spike barely uses document structure beyond dests.

## How links were checked

No GUI click-through. After `press`, `pypdf` was used to:

- Confirm dest page numbers (cover=1, year=2, Q1=3, January=7, first week=19,
  1 Jan=72, 31 Dec=436).
- Confirm the year-page nav strip is five bottom rectangles targeting those
  section landings, and the cover has **no** bottom-strip annots (only the
  year numeral → year page).
- Confirm the year-page January title → page 7 and Jan 1–4 cells → pages 72–75.
- Confirm the January grid has taps to `day-2026-01-01` and the first week.

Pages were also rasterized with `pdftoppm` to check chrome (nav present except
cover; active tab wash).

## Verdict for the question

If the goal is **a working linked yearly PDF on one canvas**, fpdf2 is enough
and the code stays small. If the goal is **many devices, MOS/rail, Typst-quality
type, and a house style**, starting here means re-inventing a layout engine
that Typst already is. The Ruby/Typst decisions were not the cost of PDF
links; they were the cost of treating the planner as a designed document.
This branch treats it as rectangles with destinations. That is a valid
product, just a different one.
