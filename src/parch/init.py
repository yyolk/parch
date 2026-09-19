"""Write a starter TOML. ``parch init --fetch`` pulls examples/nomad.toml from GitHub."""

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from parch import ConfigError, FetchError

# Examples are not in the wheel. Pin GitHub raw on master (not a release asset).
STARTER_URL = "https://raw.githubusercontent.com/yyolk/parch/master/examples/nomad.toml"
DEFAULT_DEST = Path("nomad.toml")
FETCH_TIMEOUT_S = 15


def fetch_starter(url: str = STARTER_URL, timeout: float = FETCH_TIMEOUT_S) -> str:
    """GET ``url`` as UTF-8 text. Fail loudly on HTTP/network/empty body."""
    request = Request(url, headers={"User-Agent": "parch"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        raise FetchError(f"fetch failed: HTTP {exc.code} from {url}") from exc
    except TimeoutError as exc:
        raise FetchError(
            f"fetch failed: timed out ({url}; need network for --fetch)"
        ) from exc
    except URLError as exc:
        raise FetchError(
            f"fetch failed: {exc.reason} ({url}; need network for --fetch)"
        ) from exc
    text = raw.decode("utf-8")
    if not text.strip():
        raise FetchError(f"fetch failed: empty body from {url}")
    return text


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
        description="Write a starter TOML. --fetch downloads examples/nomad.toml from GitHub.",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Download the pinned starter TOML from GitHub raw (examples/nomad.toml on master).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_DEST),
        help="Destination path (default: nomad.toml).",
    )
    args = parser.parse_args(argv)
    if not args.fetch:
        print(
            "parch: init requires --fetch (downloads examples/nomad.toml from GitHub; not in the wheel)",
            file=sys.stderr,
        )
        return 2
    dest = Path(args.output)
    try:
        if dest.exists():
            raise ConfigError(f"refusing to overwrite {dest}")
        text = fetch_starter()
        path = write_starter(dest, text)
    except (ConfigError, FetchError) as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0
