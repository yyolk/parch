# Notes-pages benchmark (ReportLab spike)

**DO NOT MERGE.** Full-year **2026**, Monday weeks, 106 × 144 mm. One Python
process (`press --notes-pages N`) writes the PDF. No Typst, no fpdf2.

Model: **1 daily page + N dedicated lined notes pages per day**.
`N=0` is the original book (notes panel on the day page only).

## How it was measured

- Host: this Cloud Agent VM, **15 GiB RAM**, 4 CPUs, **no swap**.
- Command: `/usr/bin/time -v` wrapping `.venv/bin/press --year 2026 --notes-pages N`.
- Wall time and peak RSS are **generate only** (not the later pypdf inspect).
- Page / dest / annot counts: `pypdf` after a successful write.
- **Named dests:** ReportLab `bookmarkPage` objects are published on the catalog
  as `/Dests` (name → `[page /Fit]`). `pypdf.named_destinations` lists them with
  a leading slash (`/day-2026-07-02`). Count = `len(reader.named_destinations)`.
  Link annots = page `/Annots` with `/Subtype /Link`.
- Order: 0 → 2 → 10 → 20 → 30 → 50 → 100. Stop on OOM/SIGKILL (none died).
- Full-year PDFs for N≥2 were **deleted after measuring** (N=100 was ~109 MB).
- Machine log: `artifacts/bench-notes.json`.
- Runner: `scripts/bench_notes.py`.

## Results

| N (notes pages / day) | total PDF pages | wall time | peak RSS (`time -v`) | PDF bytes | # link annots | # named dests |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 (baseline) | 436 | 1.25 s | 55.6 MiB (56 924 KB) | 4 258 680 | 18 259 | 436 |
| 2 | 1 166 | 1.87 s | 73.1 MiB (74 852 KB) | 6 206 462 | 24 099 | 1 166 |
| 10 | 4 086 | 4.40 s | 138.4 MiB (141 688 KB) | 14 535 107 | 50 379 | 4 086 |
| 20 | 7 736 | 7.76 s | 224.5 MiB (229 876 KB) | 24 954 951 | 83 229 | 7 736 |
| 30 | 11 386 | 11.29 s | 297.5 MiB (304 652 KB) | 35 478 105 | 116 079 | 11 386 |
| 50 | 18 686 | 17.84 s | 472.7 MiB (484 060 KB) | 56 518 298 | 181 779 | 18 686 |
| 100 | 36 936 | 34.60 s | 892.6 MiB (914 064 KB) | 109 129 706 | 346 029 | 36 936 |

No run was OOM-killed, SIGKILL’d, or allocator-failed. Last completed **N=100**.
Died N: **none**.

Page count matches `71 + 365 × (1 + N)` (cover + year + 4 quarters + 12 months
+ 53 weeks + one day page + N notes pages for each of 365 days). Named dest
count equals page count (one `bookmarkPage` per page).

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

## vs fpdf2 spike (PR #204)

Same VM class (15 GiB, 4 CPU, no swap), same page model, same `/usr/bin/time -v`
around `press`. fpdf2 numbers copied from that branch’s `BENCH.md`.

| N | pages | wall RL | wall fpdf2 | RSS RL | RSS fpdf2 | bytes RL | bytes fpdf2 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 436 | 1.25 s | 1.36 s | 55.6 | 65.6 | 4.3 MB | 2.6 MB |
| 2 | 1 166 | 1.87 s | 2.01 s | 73.1 | 76.6 | 6.2 MB | 4.1 MB |
| 10 | 4 086 | 4.40 s | 4.32 s | 138 | 122 | 14.5 MB | 10.1 MB |
| 20 | 7 736 | 7.76 s | 7.42 s | 225 | 178 | 25.0 MB | 17.6 MB |
| 30 | 11 386 | 11.29 s | 10.21 s | 298 | 233 | 35.5 MB | 25.1 MB |
| 50 | 18 686 | 17.84 s | 16.07 s | 473 | 346 | 56.5 MB | 40.1 MB |
| 100 | 36 936 | 34.60 s | 31.20 s | 893 | 629 | 109 MB | 77.7 MB |

Link annots are in the same ballpark (RL 18 259 vs fpdf2 16 937 at N=0;
346 029 vs 345 072 at N=100). Dest counts differ because this spike emits
exactly one catalog dest per page; fpdf2 reserved a few extra names (440 vs
436 at N=0).

## Scaling

RSS and wall time are close to **linear in N**. From N=0 → N=100, peak RSS
grew ~837 MiB across ~36 500 extra notes pages: on the order of **23 KB RSS
per extra notes page** (fpdf2 was ~15 KB). Wall time ~0.33 s per increment of
N (365 extra pages). CPU sat at ~99% during emit.

PDFs are **fatter** than fpdf2 at every N (~1.4× at N=0, ~1.4× at N=100).
ReportLab’s object graph and `/Dests` dictionary show up on disk.

## Verdict

Python/ReportLab **holds**. Day↔notes linking at N=2 is cheap (1.9 s, 73 MiB).
N=10–20 is still a laptop-idle generate (4–8 s, 138–225 MiB). N=100 (36 936
pages, 346k link annots, 37k named dests) finished in **35 s at 893 MiB**,
well under this VM’s 15 GiB and with no Typst-like notes-slab RSS cliff.

Compared with fpdf2 on the same matrix: **same order of magnitude**, slightly
slower and hungrier at the top end, larger files. Cost is still bytes-on-disk
and annotation volume, not a layout solver. If parch’s pain was Typst
measuring/relayout of a notes slab, this path does not reproduce it either.
