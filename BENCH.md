# Notes-pages benchmark (fpdf2 spike)

**DO NOT MERGE.** Full-year **2026**, Monday weeks, 106 × 144 mm. One Python
process (`press --notes-pages N`) writes the PDF. No Typst.

Model: **1 daily page + N dedicated lined notes pages per day**.
`N=0` is the original book (notes panel on the day page only).

## How it was measured

- Host: this Cloud Agent VM, **15 GiB RAM**, 4 CPUs, **no swap**.
- Command: `/usr/bin/time -v` wrapping `.venv/bin/press --year 2026 --notes-pages N`.
- Wall time and peak RSS are **generate only** (not the later pypdf inspect).
- Page / dest / annot counts: `pypdf` after a successful write.
- Order: 0 → 2 → 10 → 20 → 30 → 50 → 100. Stop on OOM/SIGKILL (none died).
- Full-year PDFs for N≥2 were **deleted after measuring** (N=100 was ~78 MB).
- Machine log: `artifacts/bench-notes.json`.
- Runner: `scripts/bench_notes.py`.

## Results

| N (notes pages / day) | total PDF pages | wall time | peak RSS (`time -v`) | PDF bytes | # link annots | # named dests |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 (baseline) | 436 | 1.36 s | 65.6 MiB (67 160 KB) | 2 637 635 | 16 937 | 440 |
| 2 | 1 166 | 2.01 s | 76.6 MiB (78 484 KB) | 4 095 742 | 23 142 | 1 170 |
| 10 | 4 086 | 4.32 s | 121.7 MiB (124 648 KB) | 10 075 167 | 49 422 | 4 090 |
| 20 | 7 736 | 7.42 s | 178.4 MiB (182 668 KB) | 17 596 869 | 82 272 | 7 740 |
| 30 | 11 386 | 10.21 s | 233.4 MiB (238 964 KB) | 25 112 540 | 115 122 | 11 390 |
| 50 | 18 686 | 16.07 s | 346.4 MiB (354 724 KB) | 40 140 098 | 180 822 | 18 690 |
| 100 | 36 936 | 31.20 s | 628.7 MiB (643 784 KB) | 77 739 276 | 345 072 | 36 940 |

No run was OOM-killed, SIGKILL’d, or allocator-failed. Last completed **N=100**.
Died N: **none**.

Page count matches `71 + 365 × (1 + N)` (cover + year + 4 quarters + 12 months
+ 53 weeks + one day page + N notes pages for each of 365 days).

## Spot-check (`pypdf`, mid-year 2026-07-02)

| N | `day-2026-07-02` | `…-notes-1` | day → notes-1 | notes-1 → day |
| ---: | ---: | ---: | :---: | :---: |
| 0 | page 254 | (none, expected) | — | — |
| 2 | 618 | 619 | yes | yes |
| 10 | 2074 | 2075 | yes | yes |
| 20 | 3894 | 3895 | yes | yes |
| 30 | 5714 | 5715 | yes | yes |
| 50 | 9354 | 9355 | yes | yes |
| 100 | 18454 | 18455 | yes | yes |

Specimen with N=2 (8 pages, committed): `artifacts/specimen-2026-notes2.pdf`.

## Scaling

RSS and wall time are close to **linear in N** (and in page count). From N=0 →
N=100, peak RSS grew ~563 MiB across ~36 500 extra notes pages: on the order of
**15 KB RSS per extra notes page**. Wall time ~0.3 s per increment of N
(365 extra pages). CPU sat at ~99%; this is emit + `output()`, not a layout
solver.

## Verdict

Python/fpdf2 **just holds**. Day↔notes linking at N=2 is cheap (2 s, 77 MiB).
N=10–20 is still a laptop-idle generate (4–7 s, 122–178 MiB). The obscene
points — N=30, 50, **100** (36 936 pages, 345k link annots, 37k named dests) —
finished in **31 s at 629 MiB**, well under this VM’s 15 GiB and with no
Typst-like notes-slab RSS cliff. Cost is bytes-on-disk and annotation volume,
not layout memory. If parch’s pain was Typst measuring/relayout of a notes
slab, this path does not reproduce it: each notes page is a header, three
chips, a lined `rect`, and a handful of page links.
