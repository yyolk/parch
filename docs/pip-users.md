# The pip-user problem

`uv tool install parch` and `pip install parch` put the `parch` console script on `PATH`. They do **not** unpack [`examples/`](https://github.com/yyolk/parch/tree/master/examples). Those TOMLs are repo files, not wheel package data.

So a PyPI user can press the sealed default:

```shell
parch press -o nomad-2026.pdf
```

…but anything else (`device`, `months`, `book`, daily schedule, …) needs a spec file they do not have unless they clone the repo or write one from scratch.

This page is the docs-site answer: host a [cookbook](cookbook.md) on Pages and let them download a handwritten sample.

<a href="../downloads/nomad.toml" download="nomad.toml">Download nomad.toml</a> — Nomad 2026 year planner. Then:

```shell
parch press nomad.toml -o nomad-2026.pdf
```

Other exploratories in this cluster (package-data samples, `init`, `--write-config`) are CLI-side answers to the same hole. This tree does not ship TOML inside the wheel.
