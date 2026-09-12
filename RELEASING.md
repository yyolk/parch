# Releasing

Happy path:

1. **Actions → Bump version** — pick `patch` / `minor` / `major` and **publish** (default) vs draft.
2. Merge the `bump/v…` PR when CI is green.
3. **Cut release** creates the GitHub Release (draft or published) immediately — it does not wait for post-merge Pages CI. It uses `GITHUB_TOKEN`, which does not fire `on: release` workflows, so a **published** cut then `workflow_dispatch`es **Publish** (TestPyPI + PyPI, with `release_tag`) and **Release PDFs** (`release_tag`). A draft does not dispatch those; publishing the draft in the UI still fires `on: release` normally.

A published GitHub Release is the ship step. Tag `vX.Y.Z` must match `[project].version` in `pyproject.toml` (no `v` in the file). Hatchling embeds that file version on the tagged commit; **Publish** fails the build if the tag and file differ.

Every published Release goes to [TestPyPI](https://test.pypi.org/project/parch/). A stable Release (pre-release unchecked) also waits on the `pypi` environment, then uploads to [PyPI](https://pypi.org/project/parch/). The wheel and sdist attach to that Release. Draft Releases do not start **Publish** or **Release PDFs** until someone publishes the draft in the UI.

Do not `git push origin vX.Y.Z` to ship. Never retag.

Manual TestPyPI-only: **Actions → Publish → `testpypi`**.

## Release PDFs

Published Releases also run **Release PDFs**, which presses each pressable device and attaches `parch-<version>-<device>.pdf` (e.g. `parch-0.x.y-supernote-nomad.pdf`). Separate from **Publish**: it does not block or gate PyPI. Specimens stay on Pages (`parch specimen` / CI Pages); these product PDFs do not.

The matrix is `{device}` shards from `parch.services.release_pdfs` (`PRESSABLE_DEVICE_IDS` — Nomad-only; not `known_device_ids()`). Each shard presses the TOML mapped for that device (`supernote-nomad` → `examples/nomad.toml`). Kindle Scribe is in the registry and can be pressed via `examples/scribe.toml`; it is not a release-PDF shard yet.

To time a run without a new tag: **Actions → Release PDFs → Run workflow**. Leave `release_tag` empty (press + job artifacts only, no `gh release upload`). The PDF filename then uses `[project].version` from the checkout. `max-parallel` defaults to the shard count; set `max_parallel` to override. Set `release_tag` (e.g. `v0.2.7`) to attach to an existing Release; the filename version is that tag with `v` stripped, not the checkout's pyproject version.

## Version bumps

**Bump version** runs `uv version --bump` (do not hand-edit the field), opens a ready-for-review `bump/vX.Y.Z` PR, and labels it `release:publish` or `release:draft`. Merging that PR is what **Cut release** watches.

`uv version` writes `[project].version`. Exact string: `uv version 0.1.2rc1 --no-sync`. `parch --version` and `__version__` read the installed package metadata, not a second string.

Manual bump (pre-releases, or when you are not using the workflow):

```shell
uv version --short                          # current, e.g. 0.1.1
uv version --bump patch --no-sync           # 0.1.1 => 0.1.2
uv version --bump minor --no-sync           # 0.1.1 => 0.2.0
uv version --bump major --no-sync           # 0.1.1 => 1.0.0
uv version --dry-run --bump patch           # print next, do not write
```

`--no-sync` skips rewriting the venv; the file is the point. Commit that `pyproject.toml` (and the lockfile if `uv version` touched it) and open the bump PR.

The Release tag is `v` plus `uv version --short` after the bump.

## Pre-release

**Bump version** is `patch` / `minor` / `major` only. Pre-releases stay a manual `uv version` recipe. **Cut release** creates a normal (not pre-release) GitHub Release, so do not use that path for rc/alpha/beta.

Same loop as stable. The version string is a PEP 440 pre-release and the GitHub Release has **Set as a pre-release** checked. TestPyPI gets it; PyPI does not.

From `0.1.1`:

```shell
# first rc of the next patch
uv version --bump patch --bump rc --no-sync
# 0.1.1 => 0.1.2rc1

# another rc of the same version
uv version --bump rc --no-sync
# 0.1.2rc1 => 0.1.2rc2

# drop the suffix when that cut is good
uv version --bump stable --no-sync
# 0.1.2rc2 => 0.1.2
```

`--bump alpha` / `--bump beta` work the same way as `--bump rc`.

1. Merge the bump PR (`0.1.2rc1`) to `master`. Wait for CI.
2. Draft a Release. Tag `v0.1.2rc1` (create on publish), target `master`, tick **Set as a pre-release**.
3. Publish. TestPyPI gets `0.1.2rc1`. The `pypi` environment is skipped. Wheel and sdist attach.

Stable later is another bump PR (`uv version --bump stable`) and a new Release `v0.1.2` with the box unchecked. Do not reuse `0.1.2rc1`. Do not un-tick pre-release on the same tag. Do not publish `0.1.2` to TestPyPI as a pre-release and then the same `0.1.2` to PyPI.
