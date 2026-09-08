# Notes-pages benchmark (fpdf2 spike v2)

**DO NOT MERGE.** Full-year **2026**, Monday weeks, 106 × 144 mm. One Python
process (`press --notes-pages N`) writes the PDF. No Typst.

Model: **1 daily page + N dedicated lined notes pages per day**.
`N=0` is the original book (notes panel on the day page only).

## How it was measured

- Host: this Cloud Agent VM, **15 GiB RAM**, 4 CPUs, **no swap**.
- Command: `/usr/bin/time -v` wrapping `.venv/bin/press --year 2026 --notes-pages N`.
- Wall time and peak RSS are **generate only** (not the later pypdf inspect).
- Page / dest / annot counts: `pypdf` after a successful write.
- **Named dests:** fpdf2 `set_link(name=…)` on each page, published as a
  catalog Names/Dests name tree. Count = `len(reader.named_destinations)`.
  Link annots = page `/Annots` with `/Subtype /Link`.
- Order: 0 → 2 → 10 → 20 → 30 → 50 → 100. Stop on OOM/SIGKILL (none died).
- Full-year PDFs for N≥2 were **deleted after measuring** (N=100 was ~76 MB).
- Machine log: `artifacts/bench-notes.json`.
- Runner: `scripts/bench_notes.py`.

## Results

| N (notes pages / day) | total PDF pages | wall time | peak RSS (`time -v`) | PDF bytes | # link annots | # named dests |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 (baseline) | 436 | 1.23 s | 63.6 MiB (65 084 KB) | 3 137 663 | 20 065 | 436 |
| 2 | 1 166 | 1.73 s | 72.7 MiB (74 408 KB) | 4 613 785 | 25 905 | 1 166 |
| 10 | 4 086 | 3.54 s | 109.2 MiB (111 812 KB) | 10 340 584 | 48 900 | 4 086 |
| 20 | 7 736 | 6.05 s | 154.4 MiB (158 116 KB) | 17 609 786 | 78 100 | 7 736 |
| 30 | 11 386 | 8.46 s | 200.5 MiB (205 280 KB) | 24 873 406 | 107 300 | 11 386 |
| 50 | 18 686 | 13.52 s | 290.3 MiB (297 304 KB) | 39 394 586 | 165 700 | 18 686 |
| 100 | 36 936 | 26.04 s | 518.0 MiB (530 472 KB) | 75 737 364 | 311 700 | 36 936 |

No run was OOM-killed, SIGKILL’d, or allocator-failed. Last completed **N=100**.
Died N: **none**.

Page count matches `71 + 365 × (1 + N)` (cover + year + 4 quarters + 12 months
+ 53 weeks + one day page + N notes pages for each of 365 days). Named dest
count equals page count (one `set_link(name=…)` per page).

## Spot-check (`pypdf`, mid-year 2026-07-02)

| N | `day-2026-07-02` | `…-notes-1` | day → notes-1 | notes-1 → day |
| ---: | ---: | :---: | :---: | :---: |
| 0 | page 254 | (none, expected) | — | — |
| 2 | 618 | 619 | yes | yes |
| 10 | 2074 | 2075 | yes | yes |
| 20 | 3894 | 3895 | yes | yes |
| 30 | 5714 | 5715 | yes | yes |
| 50 | 9354 | 9355 | yes | yes |
| 100 | 18454 | 18455 | yes | yes |

Specimen with N=2 (8 pages, committed): `artifacts/specimen-2026-notes2.pdf`.

## vs fpdf2 v1 (PR #204) and ReportLab (PR #205)

Same VM class (15 GiB, 4 CPU, no swap), same page model, same `/usr/bin/time -v`
around `press`. Prior numbers copied from those branches’ `BENCH.md`.

| N | pages | wall v2 | wall v1 | wall RL | RSS v2 | RSS v1 | RSS RL | bytes v2 | bytes v1 | bytes RL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 436 | 1.23 s | 1.36 s | 1.25 s | 63.6 | 65.6 | 55.6 | 3.1 MB | 2.6 MB | 4.3 MB |
| 2 | 1 166 | 1.73 s | 2.01 s | 1.87 s | 72.7 | 76.6 | 73.1 | 4.6 MB | 4.1 MB | 6.2 MB |
| 10 | 4 086 | 3.54 s | 4.32 s | 4.40 s | 109 | 122 | 138 | 10.3 MB | 10.1 MB | 14.5 MB |
| 20 | 7 736 | 6.05 s | 7.42 s | 7.76 s | 154 | 178 | 225 | 17.6 MB | 17.6 MB | 25.0 MB |
| 30 | 11 386 | 8.46 s | 10.21 s | 11.29 s | 201 | 233 | 298 | 24.9 MB | 25.1 MB | 35.5 MB |
| 50 | 18 686 | 13.52 s | 16.07 s | 17.84 s | 290 | 346 | 473 | 39.4 MB | 40.1 MB | 56.5 MB |
| 100 | 36 936 | 26.04 s | 31.20 s | 34.60 s | 518 | 629 | 893 | 75.7 MB | 77.7 MB | 109 MB |

Link annots at N=0: v2 20 065 / v1 16 937 / RL 18 259 (v2 stamps more calendar
cells). At N=100: v2 311 700 / v1 345 072 / RL 346 029 — notes pages here carry
fewer chrome taps (day / prev / next chips only). Dest counts: v2 and RL equal
page count; v1 reserved a few extras (440 vs 436 at N=0).

## Scaling

RSS and wall time are close to **linear in N**. From N=0 → N=100, peak RSS
grew ~454 MiB across ~36 500 extra notes pages: on the order of **13 KB RSS
per extra notes page** (v1 was ~15 KB; ReportLab ~23 KB). Wall time ~0.25 s
per increment of N (365 extra pages).

## Verdict

Python/fpdf2 v2 **just holds**, same class as v1 and ReportLab. Day↔notes at
N=2 is cheap (1.7 s, 73 MiB). N=10–20 is a few seconds. N=100 (36 936 pages)
finished in **26 s at 518 MiB** — a bit leaner and faster than v1, clearly
under ReportLab’s 35 s / 893 MiB, and nowhere near a Typst notes-slab cliff.
Cost is still disk and annotation volume, not layout memory. Tighter drawing
did not cost a memory regime change.
