"""Equal or weighted tracks inside a parent rect. Pure geom — no calendar knowledge."""

from parch.geom import Rect


def _shares(n: int, weights: tuple[float, ...] | None) -> tuple[float, ...]:
    if n < 1:
        raise ValueError(f"n must be >= 1, not {n}")
    if weights is None:
        return tuple(1.0 for _ in range(n))
    if len(weights) != n:
        raise ValueError(f"weights length {len(weights)} != n {n}")
    if any(weight < 0 for weight in weights):
        raise ValueError("weights must be >= 0")
    if sum(weights) <= 0:
        raise ValueError("weights must sum to > 0")
    return weights


def columns(
    parent: Rect,
    n: int,
    *,
    gap: float = 0,
    weights: tuple[float, ...] | None = None,
) -> tuple[Rect, ...]:
    shares = _shares(n, weights)
    if gap < 0:
        raise ValueError(f"gap must be >= 0, not {gap}")
    inner = parent.w - gap * (n - 1)
    if inner < 0:
        raise ValueError("gaps exceed parent width")
    total = sum(shares)
    x = parent.x
    out: list[Rect] = []
    for share in shares:
        width = inner * (share / total)
        out.append(Rect(x, parent.y, width, parent.h))
        x += width + gap
    return tuple(out)


def rows(
    parent: Rect,
    n: int,
    *,
    gap: float = 0,
    weights: tuple[float, ...] | None = None,
) -> tuple[Rect, ...]:
    shares = _shares(n, weights)
    if gap < 0:
        raise ValueError(f"gap must be >= 0, not {gap}")
    inner = parent.h - gap * (n - 1)
    if inner < 0:
        raise ValueError("gaps exceed parent height")
    total = sum(shares)
    y = parent.y
    out: list[Rect] = []
    for share in shares:
        height = inner * (share / total)
        out.append(Rect(parent.x, y, parent.w, height))
        y += height + gap
    return tuple(out)
