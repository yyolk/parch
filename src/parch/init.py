"""Write a starter TOML. ``parch init --from-release`` pulls the Release zip."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from parch import ConfigError, FetchError, __version__
from parch.services.examples_zip import EXAMPLES_ZIP_NAME, starters_from_zip

REPO = "yyolk/parch"
DEFAULT_STARTER = "nomad"
FETCH_TIMEOUT_S = 15


def release_tag(version: str | None = None) -> str:
    """GitHub Release tag for the installed package version (``v`` + version)."""
    ver = __version__ if version is None else version
    if not ver or ver == "unknown":
        raise FetchError("cannot resolve release tag (package version unknown)")
    return f"v{ver.removeprefix('v')}"


def examples_zip_url(tag: str | None = None) -> str:
    """Download URL for ``parch-examples.zip`` on ``tag`` (installed version)."""
    resolved = release_tag() if tag is None else tag
    return f"https://github.com/{REPO}/releases/download/{resolved}/{EXAMPLES_ZIP_NAME}"


def fetch_examples_zip(
    url: str | None = None, timeout: float = FETCH_TIMEOUT_S
) -> bytes:
    """GET the Release zip. Fail loudly on HTTP / network / empty body."""
    resolved_url = examples_zip_url() if url is None else url
    request = Request(resolved_url, headers={"User-Agent": "parch"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        tag = release_tag()
        if exc.code == 404:
            raise FetchError(
                f"fetch failed: {EXAMPLES_ZIP_NAME} missing on {tag} "
                f"({resolved_url}; need network for --from-release)"
            ) from exc
        raise FetchError(
            f"fetch failed: HTTP {exc.code} from {resolved_url}; "
            "need network for --from-release"
        ) from exc
    except TimeoutError as exc:
        raise FetchError(
            f"fetch failed: timed out ({resolved_url}; need network for --from-release)"
        ) from exc
    except URLError as exc:
        raise FetchError(
            f"fetch failed: {exc.reason} ({resolved_url}; need network for --from-release)"
        ) from exc
    if not raw:
        raise FetchError(f"fetch failed: empty body from {resolved_url}")
    return raw


def extract_starter(data: bytes, starter: str) -> bytes:
    """Return TOML bytes for ``starter`` from a ``parch-examples.zip`` body."""
    starters = starters_from_zip(data)
    try:
        return starters[starter]
    except KeyError as exc:
        available = ", ".join(sorted(starters))
        raise ConfigError(
            f"unknown starter {starter!r}; available: {available}"
        ) from exc


def write_starter(dest: Path, text: str) -> Path:
    """Write ``text`` to ``dest``. Refuse to overwrite an existing path."""
    if dest.exists():
        raise ConfigError(f"refusing to overwrite {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch init",
        description=(
            "Write a starter TOML. --from-release downloads parch-examples.zip "
            "for this install's Release tag."
        ),
    )
    parser.add_argument(
        "--from-release",
        action="store_true",
        help=(
            f"Download {EXAMPLES_ZIP_NAME} for the installed version's tag "
            "and extract a starter."
        ),
    )
    parser.add_argument(
        "--starter",
        default=DEFAULT_STARTER,
        help=f"Starter name (toml stem in the zip). Default: {DEFAULT_STARTER}.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List starters in the Release zip and exit (still needs --from-release).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Destination path (default: <starter>.toml).",
    )
    args = parser.parse_args(argv)
    if not args.from_release:
        print(
            "parch: init requires --from-release "
            f"(downloads {EXAMPLES_ZIP_NAME} for the installed version's tag; "
            "not in the wheel)",
            file=sys.stderr,
        )
        return 2
    dest = Path(args.output) if args.output else Path(f"{args.starter}.toml")
    try:
        if not args.list and dest.exists():
            raise ConfigError(f"refusing to overwrite {dest}")
        data = fetch_examples_zip()
        if args.list:
            for name in sorted(starters_from_zip(data)):
                print(name)
            return 0
        text = extract_starter(data, args.starter).decode("utf-8")
        if not text.strip():
            raise FetchError(
                f"fetch failed: empty starter {args.starter!r} in {EXAMPLES_ZIP_NAME}"
            )
        path = write_starter(dest, text)
    except (ConfigError, FetchError) as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0
