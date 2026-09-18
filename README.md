<p align="center">
  <img src="docs/parch-mark-small-crushed.png" alt="parch" width="160">
</p>

# parch

[![PyPI](https://img.shields.io/pypi/v/parch.svg)](https://pypi.org/project/parch/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/yyolk/parch/actions/workflows/ci.yml/badge.svg)](https://github.com/yyolk/parch/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

parch generates **fixed e-ink PDF pages**. The MVP target is SuperNote Nomad only.

## Install / Press

Needs [uv](https://docs.astral.sh/uv/) and Python 3.14+.

```shell
uv sync --group dev
uv run parch press examples/nomad.toml -o out/nomad-2026.pdf
uv run parch specimen -w out   # PNG catalog (Nomad + Scribe); click a thumb to expand in place
uv run parch proof examples/nomad.toml -o out/exp-typeramp-proof.pdf
```

## Architecture

```
Device → Component (data only) → Section (build Page) → Layout (chrome + seat) → Plotter → Press
```

| Device | id | size | resolution | notes |
| --- | --- | --- | --- | --- |
| SuperNote Nomad | `supernote-nomad` | 118.87 × 158.5 mm | 1404×1872 @ 300 PPI | top clearance 8 mm reserved; writing clearance 4 mm; `root_body` 8.5pt |

## Tests

```shell
uv run pytest
uv run ruff check src tests && uv run ruff format --check src tests
```

## Releasing

Ship steps live in [Releasing](RELEASING.md).

## License / Credits

MIT — see [LICENSE](LICENSE).

Historical inspiration: [Vitaliy Kudryk’s LYP](https://github.com/kudrykv/latex-yearly-planner). fpdf2 Plotter rewrite; not a port of LYP sources.

Runtime dependency [fpdf2](https://github.com/py-pdf/fpdf2) is LGPL-3.0, separate from this MIT license.

Vendored [Jost](https://indestructibletype.com/Jost.html) (Book / Medium / Bold / Heavy) is SIL OFL 1.1 — see `src/parch/fonts/LICENSE`.
