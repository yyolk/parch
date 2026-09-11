"""Press a spec to a PDF. CLI and ``python -m parch``."""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from parch import ConfigError
from parch.books.year_planner import YearPlanner
from parch.devices import get_device
from parch.fonts import (
    PROOF_PROFILE,
    ProofProfile,
    TypeOverlay,
    bind_ramp,
    compose_overlays,
    require_overlay,
)
from parch.fonts.ramp import OverlayData
from parch.plotter.fpdf2 import Fpdf2Plotter
from parch.plotter.protocol import Plotter
from parch.spec import Spec

_DEVICE_TOKENS = {"supernote-nomad", "nomad"}


def merge_press_overlay(
    spec: Spec,
    overlay: OverlayData | None = None,
    proof: bool | ProofProfile = False,
) -> TypeOverlay:
    """``toml ⊕ proof ⊕ press kwarg`` — later explicit fields win.

    Each layer is validated (exact ``schema_version``, closed TypeSteps, Jost
    weights, size bands) before compose. Defaults live in ``EffectiveRamp``.
    This returns the composed overlay only. ``proof=True`` selects
    ``PROOF_PROFILE``; ``proof=ProofProfile(...)`` uses that instance.
    """
    toml_overlay = require_overlay(spec.type_overlay)
    proof_layer = _proof_overlay(proof)
    proof_overlay = TypeOverlay() if proof_layer is None else require_overlay(proof_layer)
    press_overlay = TypeOverlay() if overlay is None else require_overlay(overlay)
    return require_overlay(compose_overlays(toml_overlay, proof_overlay, press_overlay))


def press(
    spec: Spec,
    output: Path,
    plotter: Plotter | None = None,
    overlay: OverlayData | None = None,
    proof: bool | ProofProfile = False,
) -> Path:
    """Build the MVP book and write ``output``.

    Press **validates** spec TOML ⊕ proof ⊕ press overlay (pure
    ``require_overlay``, exact ``schema_version`` match) before
    ``bind_ramp`` builds

        EffectiveRamp = defaults ⊕ toml ⊕ proof (if on)

    at ``device.root_body``. Overlay size is an absolute override for
    that step; it does not change root or sibling steps.

    A bad overlay raises ``ConfigError`` before paint. ``proof=True``
    selects ``PROOF_PROFILE``. ``proof=ProofProfile(...)`` uses that
    instance.

    Invoke::

        press(spec, out, proof=True)
        parch proof examples/mvp.toml -o out.pdf
        parch press examples/mvp.toml --proof -o out.pdf

    Painters never read the overlay. They pass ``TypeRef`` / ink on the
    closed TypeStep ladder. ``family`` stays on ``TypeInk``.
    """
    device = get_device(spec.device)
    resolved = bind_ramp(
        overlay=merge_press_overlay(spec, overlay, proof),
        root_body=device.root_body,
    )
    if plotter is None:
        plotter = Fpdf2Plotter(device, catalog=resolved.catalog, ramp=resolved)
    YearPlanner(ramp=resolved).plot(spec, plotter)
    plotter.finish(output)
    return output


def _proof_overlay(proof: bool | ProofProfile) -> TypeOverlay | None:
    match proof:
        case False:
            return None
        case True:
            return PROOF_PROFILE.overlay
        case ProofProfile() as profile:
            return profile.overlay
        case _:
            raise TypeError(f"proof must be bool or ProofProfile, not {type(proof)!r}")


def _load_spec(token: str | None, *, year: int | None, month: int | None) -> Spec:
    match token:
        case None:
            spec = Spec()
        case device if device in _DEVICE_TOKENS:
            spec = Spec(device=device)
        case path_text if Path(path_text).is_file():
            spec = Spec.from_path(Path(path_text))
        case _:
            raise ConfigError(f"spec file not found: {token}")
    updates: dict[str, object] = {}
    if year is not None:
        updates["year"] = year
    if month is not None:
        updates["months"] = (month,)
    return replace(spec, **updates) if updates else spec


def _outputs(args: argparse.Namespace, spec_token: str | None) -> list[Path]:
    paths: list[Path] = []
    if args.workdir:
        paths.append(Path(args.workdir) / "index.pdf")
    if args.output:
        paths.append(Path(args.output))
    if paths:
        return paths
    if spec_token and spec_token not in _DEVICE_TOKENS and Path(spec_token).is_file():
        return [Path(spec_token).with_suffix(".pdf")]
    return [Path("parch.pdf")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch",
        description="Press fixed e-ink PDF pages (greenfield MVP).",
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default=None,
        help="TOML spec path, or device id (supernote-nomad). Default: Nomad 2026 MVP.",
    )
    parser.add_argument("-o", "--output", help="Product PDF path.")
    parser.add_argument("-w", "--workdir", help="Also write workdir/index.pdf.")
    parser.add_argument("--year", type=int, help="Overlay planner year.")
    parser.add_argument("--month", type=int, help="MVP month (1–12).")
    parser.add_argument(
        "--proof",
        action="store_true",
        help="Apply ProofProfile overlay (slightly larger chrome/title for on-screen review).",
    )
    # Accept a leading `press`, `proof`, or `specimen` verb. `parch proof` is
    # the historical on-screen path; it selects ProofProfile. `parch specimen`
    # writes a static PNG catalog (not a product PDF).
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] == "specimen":
        from parch.specimen import main as specimen_main

        return specimen_main(raw[1:])
    proof_verb = False
    if raw and raw[0] in {"press", "proof"}:
        proof_verb = raw[0] == "proof"
        raw = raw[1:]
    args = parser.parse_args(raw)
    try:
        spec = _load_spec(args.spec, year=args.year, month=args.month)
        outputs = _outputs(args, args.spec)
        first = press(spec, outputs[0], proof=proof_verb or args.proof)
        for extra in outputs[1:]:
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_bytes(first.read_bytes())
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    for path in outputs:
        print(path)
    return 0
