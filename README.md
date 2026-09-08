# parch

Yearly planner PDFs for e-ink, a Python port of [Vitaliy Kudryk’s LYP](https://github.com/kudrykv/latex-yearly-planner/tree/alpha).

[![PyPI](https://img.shields.io/pypi/v/parch)](https://pypi.org/project/parch/)
[![CI](https://github.com/yyolk/parch/actions/workflows/ci.yml/badge.svg)](https://github.com/yyolk/parch/actions/workflows/ci.yml)

<p>
<img src="https://yyolk.github.io/parch/158x210/dotted-left/cover.svg" alt="Cover" width="180" />
<img src="https://yyolk.github.io/parch/158x210/dotted-left/contents.svg" alt="Contents" width="180" />
<img src="https://yyolk.github.io/parch/158x210/dotted-left/monthly-jan.svg" alt="January" width="180" />
</p>

## Install

Needs [uv](https://docs.astral.sh/uv/) and Python 3.14+.

```shell
uv tool install parch
parch press supernote-nomad
```

If `typst` is not on `PATH`, press downloads official Typst v0.15.1 into `.tools/`.

## Press

```shell
parch press supernote-nomad
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `-w` / `--workdir` | (none) | Persist `index.typst` and `index.pdf` here. Without `-w`, compile in a temp dir |
| `-o` / `--output` | `./<config-stem>.pdf` | Product PDF in cwd (`mine.toml` → `./mine.pdf`). With `-w` only, dest is workdir/`index.pdf` |
| `-l` / `--locale` | `en` | Locale code |
| `-g` / `--with-ghostscript` | off | Optional PDF shrink via `gs` |
| `--debug` | off | Draw MOS debug strokes (not a config key) |
| `--year` | file year | Overlay planner year (dates and cover title; not a config key) |
| `--hand` | profile `mos.side_menu` (or left) | MOS strip side. Overlay sets `mos.side_menu` only; well stays LTR |

`--year` also rewrites the cover title year when the old year is in the title.

Full-year Nomad is one Typst document — peak RAM is page-tree count, not `index.typst` size. There is no chunked compile / PDF merge path.

`supernote-nomad` defaults to `[section.daily_notes] pages = 1` (one notes well per day; `pages = 2` is opt-in). Lean notes is **not** the 8GB fix. Other devices still default to `pages = 2`. Jobs written before this default still say `pages = 2`.

Default **8GB** Codespaces OOM on a full-year all-sections press. **16GB** works. Typst CLI peak for extras + notes=1 is ~4.0 GiB (`/usr/bin/time -f %M typst compile`, last line only). Daily page trees dominate. Python emit is ~50 MiB — not the peak. `PARCH_TYPST=py` compiles in-process, so `%M` on `uv run parch press` is Python+Typst together; `PARCH_TYPST=cli` (default) spawns `typst`, and the cgroup is Typst **plus** leftover Python/uv/OS (~2–3 GiB). Do not pipe every log line through `awk`. Press on 16GB, or omit `daily` / extras, until daily dest-tree cost drops.

```shell
parch new --device supernote-nomad --year 2027 --yes -o mine.toml
```

`--device` is a device id. Without `--yes`, `parch new` asks for device, year, sections, MOS side, paper (dotted or lined), week rail, hours, and counts/pages, then writes a complete job file. `parch edit mine.toml` reopens that file. Hand-edit still loads. Sections live in the job `sections` list. Comment a name out to disable it.

## Devices

Nineteen devices. Lined is paper (`style.scratch_pad`), not a device. MOS strip side is `mos.side_menu` (default left). Override with `--hand left|right` on `press`, `proof`, `new`, and `edit`. `--hand` does not reverse the well.

Navigation chrome is **device-gated**. `supernote-nomad` (alias `nomad`) presses **Topband**. Same canvas `118.87×158.5mm` as `supernote-a6` / `supernote-a6x`, but those ids keep **MOS**. There is no `--topband` / `--mos` switch — pick the device id (or `device` in the job TOML).

| Device | Notes |
| --- | --- |
| `supernote-nomad` | SuperNote Nomad (A6 X2). Topband; toolbar top 8mm. Alias `nomad` |
| `kindle-scribe` | Kindle Scribe. No toolbar |
| `158x210` | 158×210 mm. No toolbar |
| `supernote-manta` | SuperNote Manta (A5 X2). Toolbar top 8mm |
| `remarkable-1` | reMarkable 1. No toolbar (Scribe pack). Alias `rm1` |
| `remarkable-2` | reMarkable 2. Same 10.3" canvas as rM1; own name. Alias `rm2` |
| `remarkable-paper-pure` | reMarkable Paper Pure. Same 10.3" canvas (Carta 1300). Alias `paper-pure` |
| `remarkable-paper-pro` | reMarkable Paper Pro. No toolbar (Scribe pack). Alias `paper-pro` |
| `remarkable-paper-pro-move` | reMarkable Paper Pro Move. No toolbar (Scribe pack). Alias `paper-pro-move` |
| `supernote-a5` | SuperNote A5. Toolbar top 8mm (Nomad pack). Alias `a5` |
| `supernote-a5x` | SuperNote A5 X. Same canvas as A5; own name. Alias `a5x` |
| `supernote-a6` | SuperNote A6. Same canvas as Nomad; MOS chrome (not Topband). Alias `a6` |
| `supernote-a6x` | SuperNote A6 X. Same canvas as Nomad; MOS chrome (not Topband). Alias `a6x` |
| `kindle-scribe-11` | Kindle Scribe 11. No toolbar (Scribe pack). Alias `scribe-11` |
| `kindle-scribe-colorsoft` | Kindle Scribe Colorsoft. Same B&W canvas as Scribe 11. Alias `colorsoft` |
| `ipad-mini` | iPad mini. No toolbar (Scribe pack). Alias `mini` |
| `ipad-air-11` | iPad Air 11. No toolbar (Scribe pack). Aliases `ipad`, `air-11` |
| `ipad-pro-11` | iPad Pro 11. No toolbar (Scribe pack). Alias `pro-11` |
| `ipad-pro-13` | iPad Pro 13. No toolbar (Scribe pack). Alias `pro-13` |

## Development

```shell
uv sync
uv run pytest
```

CI runs pytest and a Nomad `parch press`. On master, CI also runs `parch specimen` for the framed devices (four paper×hand permutations each) and deploys the catalog to GitHub Pages.

Experimental: compile through the PyPI [`typst`](https://pypi.org/project/typst/) binding instead of the CLI.

```shell
uv sync --extra typst-native
PARCH_TYPST=py uv run parch press supernote-nomad
```

Or `uv tool install --with typst==0.15.0 parch`, then `PARCH_TYPST=py parch press supernote-nomad`. Default is still `cli`. There is no `auto`. The binding is 0.15.0; the CLI pin is v0.15.1.

`uv run pytest` skips the full-book comparison (`slow`). Run it with `uv run pytest -m slow -o addopts=`.

Regenerate the thumbs above with `parch specimen 158x210`.

Ship steps live in [Releasing](RELEASING.md). Hero planner PDFs (device × paper × hand) attach from `release-pdfs.yml` (not Pages, not a PyPI gate).

## License

MIT. See `LICENSE`.
