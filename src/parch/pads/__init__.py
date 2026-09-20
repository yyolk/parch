from parch import ConfigError
from parch.fonts.ramp import TypeRamp
from parch.pads.composed import Composed
from parch.pads.engineering import Engineering
from parch.pads.protocol import Pad
from parch.pads.steno import Steno
from parch.spec import Spec

__all__ = [
    "Composed",
    "Engineering",
    "Pad",
    "Steno",
    "compose",
    "pad_for",
]


def pad_for(name: str) -> type[Pad]:
    """Press selection: engineering or steno."""
    match name:
        case "engineering":
            return Engineering
        case "steno":
            return Steno
        case _:
            raise ConfigError(f"pad must be engineering or steno, not {name!r}")


def compose(spec: Spec, *, ramp: TypeRamp | None = None) -> Pad | None:
    """Pad-only stack from sheet counts, or ``None`` to keep Book press.

    ``steno_sheets > 0`` is always pad-only (no steno-notebook book).
    Year-planner ``engineering_sheets > 0`` is pad-only; ``engineering-notebook``
    stays Book (cover + faces). Both counts stack engineering then steno.
    No cover.
    """
    if spec.steno_sheets <= 0 and not (
        spec.book == "year-planner" and spec.engineering_sheets > 0
    ):
        return None
    pads: list[Pad] = []
    if spec.engineering_sheets > 0:
        pads.append(pad_for("engineering")(ramp=ramp))
    if spec.steno_sheets > 0:
        pads.append(pad_for("steno")(ramp=ramp))
    if not pads:
        return None
    if len(pads) == 1:
        return pads[0]
    return Composed(pads, ramp=ramp)
