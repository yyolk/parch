# Exploratory L — external template (copier)

Look-later spike. **Do not merge.**

`examples/` is not in the wheel. Sibling spikes fetch, package, or dump a
starter TOML. This slice asks a different question: can `parch init` stay
thin and delegate project scaffolding to an existing template tool aimed at
a **public repo** that ships those starters?

## Tool: copier (not cookiecutter)

Picked **[copier](https://copier.readthedocs.io/)** 9.6+.

| | copier | cookiecutter |
| --- | --- | --- |
| Config | `copier.yml` (YAML) | `cookiecutter.json` |
| Git src | first-class (`gh:user/repo`, HTTPS) | first-class |
| Monorepo | `_subdirectory` so this repo can be the src | template is usually its own repo |
| Non-interactive | `defaults=True` / `--defaults` | `--no-input` |
| Python API | `copier.run_copy(src, dest, …)` | `cookiecutter.main.cookiecutter` |
| Updates | `copier update` | regenerate |

Cookiecutter would work. Copier wins here because parch already *is* the
public repo that should ship starters: a root `copier.yml` with
`_subdirectory: templates/starter` makes `gh:yyolk/parch` a valid template
src without a second GitHub project. Cookiecutter wants a dedicated
template repo (or a noisy checkout of the whole tree).

## Optional extra, not a hard dep

```toml
[project.optional-dependencies]
template = ["copier>=9.6"]
```

```shell
pip install 'parch[template]'    # or: uv sync --extra template
```

Missing copier is a loud exit 2:

```
parch: init --template needs the template extra (pip install 'parch[template]' or uv sync --extra template)
```

Press / specimen / proof do not import copier.

Copier 9.18 pulls **questionary** as its own interactive prompt stack.
parch does not depend on questionary; the wrapper always passes
`defaults=True` and never opens a TTY prompt. Interactive questions stay
on `copier copy` directly.

## Command

```shell
parch init --template                 # checkout → this repo; pip → gh:yyolk/parch
parch init --template -o my-book
parch init --template gh:yyolk/parch -o my-book
parch init --template /path/to/copier-src -o my-book
```

`--template` is required. Omitting `SRC` uses this checkout when
`copier.yml` + `templates/starter/` are present, otherwise the public pin
`gh:yyolk/parch`. Dest defaults to `parch-starter/`. Existing file or
non-empty dest is refused (no `--force`).

A local git src passes `vcs_ref=HEAD` so copier does not render the latest
**tag** (which does not contain this spike). Remotes stay on copier's
default unless `--vcs-ref` is set. `gh:yyolk/parch` on master will not
have `templates/starter` until this lands — use a checkout, or
`--vcs-ref` of this branch.

The wrapper calls `copier.run_copy(..., defaults=True, overwrite=False,
quiet=True)`. No TTY prompts. Interactive questions stay on copier itself:

```shell
copier copy gh:yyolk/parch dest
```

## What the public template ships

`templates/starter/parch.toml.jinja` emits one of:

| `starter` | twin |
| --- | --- |
| `nomad` (default) | `examples/nomad.toml` |
| `scribe` | `examples/scribe.toml` |
| `extras` | `examples/nomad-extras.toml` |
| `bujo` | `examples/nomad-bujo.toml` |
| `projects` | `examples/projects.toml` |
| `engineering` | `examples/engineering.toml` |
| `steno` | `examples/steno-pad.toml` |

Year / device are copier answers (`year`, `device`). Defaults match the
twin. Copier dict choices are `{label: value}` (`Nomad year planner: nomad`).
This is a snapshot for the spike, not a live include of `examples/`.

## Out of scope

- README / version bump
- Shipping `examples/` in the wheel (exploratory A)
- `urllib` fetch of a single TOML (exploratory C)
- Questionary / `parch new` / TTY prompts (exploratory E)
- Making copier a hard dependency
- A separate `yyolk/parch-templates` repo
- `copier update` / template versioning

## Verify

```shell
uv sync --group dev
uv run pytest
uv run ruff check src tests && uv run ruff format --check src tests

uv sync --extra template
uv run parch init --template -o /tmp/parch-starter
uv run parch press /tmp/parch-starter/parch.toml -o /tmp/parch-starter/out.pdf
```
