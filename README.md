<img src="https://raw.githubusercontent.com/yyolk/parch/master/docs/parch-mark.png" alt="parch">

# parch

[![PyPI](https://img.shields.io/pypi/v/parch.svg)](https://pypi.org/project/parch/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/yyolk/parch/actions/workflows/ci.yml/badge.svg)](https://github.com/yyolk/parch/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

parch generates **fixed e-ink PDF pages**.

## Install / Press

Needs Python 3.14+.

### From PyPI

```shell
uv tool install parch          # or: pip install parch
parch press -o nomad-2026.pdf  # default: Nomad 2026 year planner
parch specimen -w out
```

No checkout needed. One-shot: `uvx parch press -o nomad-2026.pdf`. Sample TOMLs live in [`examples/`](https://github.com/yyolk/parch/tree/master/examples) (not in the wheel) — pass your own, clone, or pipe:

```shell
curl -fsSL https://raw.githubusercontent.com/yyolk/parch/master/examples/nomad.toml \
  | parch press - -o nomad-2026.pdf
```

`parch press -` reads Spec TOML from stdin (heredoc works too). A pipe with no spec token is the same as `-`.

### From a checkout

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
| Kindle Scribe (1st gen) | `kindle-scribe` | 157.48 × 209.97 mm | 1860×2480 @ 300 PPI | top clearance 8 mm reserved; writing clearance 4 mm; bottom clearance 10 mm; `root_body` 8.5pt |

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
