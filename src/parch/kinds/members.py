"""Read the strings of a closed Literal alias."""

from typing import cast, get_args


def literal_members(alias: object) -> frozenset[str]:
    """Member strings of a ``type Alias = Literal[...]`` alias."""
    value = getattr(alias, "__value__", alias)
    return frozenset(cast(tuple[str, ...], get_args(value)))
