# parch

parch generates fixed e-ink PDF pages. It requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

## Cursor Cloud specific instructions

Cloud Agent install uses `uv python install 3.14` then `uv sync --all-groups`. Re-run `uv sync --all-groups` after dependency changes; it is idempotent.

- Tests: `uv run pytest`
- Press an example: `uv run parch press examples/nomad.toml -o out/nomad.pdf` (or another file under `examples/`)
