"""Write a starter from an external copier template.

``parch init --template`` is a thin wrapper. Copier is an optional extra
(``pip install 'parch[template]'``), not a hard runtime dep. See
``docs/external-template.md``.
"""

import argparse
import sys
from pathlib import Path

from parch import ConfigError, TemplateError

# Public pin: this repo. Root copier.yml sets _subdirectory to templates/starter.
DEFAULT_PUBLIC_TEMPLATE = "gh:yyolk/parch"
DEFAULT_DEST = Path("parch-starter")
STARTER_DIR = "templates/starter"


def load_copier():
    """Import copier or raise a loud extra-missing error."""
    try:
        import copier
    except ImportError as exc:
        raise TemplateError(
            "init --template needs the template extra "
            "(pip install 'parch[template]' or uv sync --extra template)"
        ) from exc
    return copier


def checkout_root() -> Path | None:
    """Repo root when this file lives in a checkout / editable install."""
    root = Path(__file__).resolve().parents[2]
    if (root / "copier.yml").is_file() and (root / STARTER_DIR).is_dir():
        return root
    return None


def resolve_template_src(src: str | None) -> str:
    """Use an explicit src, else this checkout, else the public pin."""
    if src:
        return src
    root = checkout_root()
    if root is not None:
        return str(root)
    return DEFAULT_PUBLIC_TEMPLATE


def _is_local_git(src: str) -> bool:
    git = Path(src) / ".git"
    return git.is_dir() or git.is_file()


def apply_template(
    src: str,
    dest: Path,
    *,
    data: dict[str, object] | None = None,
    vcs_ref: str | None = None,
) -> Path:
    """Invoke ``copier.run_copy`` with defaults (non-interactive).

    Refuses a dest that already exists as a file or a non-empty directory.
    A local git src defaults to ``vcs_ref="HEAD"`` so the latest tag does
    not hide this spike's unreleased ``templates/starter``.
    """
    if dest.exists() and (dest.is_file() or any(dest.iterdir())):
        raise ConfigError(f"refusing to overwrite {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    copier = load_copier()
    kwargs: dict[str, object] = {
        "data": data or {},
        "defaults": True,
        "overwrite": False,
        "quiet": True,
    }
    ref = vcs_ref if vcs_ref is not None else ("HEAD" if _is_local_git(src) else None)
    if ref is not None:
        kwargs["vcs_ref"] = ref
    try:
        copier.run_copy(src, dest, **kwargs)
    except TemplateError:
        raise
    except Exception as exc:
        raise TemplateError(f"copier failed: {exc}") from exc
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch init",
        description=(
            "Write a starter from a copier template. "
            "--template invokes copier (optional extra, not a hard dep)."
        ),
    )
    parser.add_argument(
        "--template",
        nargs="?",
        const="",
        default=None,
        metavar="SRC",
        help=(
            "Copier src: local path, git URL, or gh:user/repo. "
            f"Omit SRC to use this checkout or {DEFAULT_PUBLIC_TEMPLATE}."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_DEST),
        help="Destination directory (default: parch-starter).",
    )
    parser.add_argument(
        "--vcs-ref",
        default=None,
        help="Copier VCS ref. Default: HEAD for a local git src; unset for remotes.",
    )
    args = parser.parse_args(argv)
    if args.template is None:
        print(
            "parch: init requires --template "
            f"(copier src; default {DEFAULT_PUBLIC_TEMPLATE}; "
            "needs pip install 'parch[template]')",
            file=sys.stderr,
        )
        return 2
    dest = Path(args.output)
    try:
        path = apply_template(
            resolve_template_src(args.template or None),
            dest,
            vcs_ref=args.vcs_ref,
        )
    except (ConfigError, TemplateError) as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0
