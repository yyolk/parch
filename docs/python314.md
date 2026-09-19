# Python 3.14 dests

`requires-python >= 3.14`. Named PDF dests are flattened t-strings in
[`src/parch/spec.py`](../src/parch/spec.py).

`_dest` walks a `string.templatelib.Template` and `match`es each part:

- `Interpolation` with a `format_spec` → `format(value, spec)`
- `Interpolation` without → `str(value)`
- `str` literal → as-is

```python
def _dest(template: Template) -> str:
    """Flatten a dest t-string (prefix + fields + format specs)."""
    chunks: list[str] = []
    for part in template:
        match part:
            case Interpolation(value=value, format_spec=spec) if spec:
                chunks.append(format(value, spec))
            case Interpolation(value=value):
                chunks.append(str(value))
            case str() as literal:
                chunks.append(literal)
    return "".join(chunks)
```

`Spec.year_dest` is the emblem:

```python
@property
def year_dest(self) -> str:
    return _dest(t"year-{self.year:04d}")
```

Default year `2026` → `"year-2026"`. Other dest properties use the same helper.
