"""parch init --from-release: Release zip for the installed tag, loud offline."""

from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from zipfile import ZipFile

import pytest

from parch import ConfigError, FetchError
from parch.init import (
    DEFAULT_STARTER,
    EXAMPLES_ZIP_NAME,
    examples_zip_url,
    extract_starter,
    fetch_examples_zip,
    main,
    release_tag,
    write_starter,
)
from parch.press import main as press_main
from parch.services.examples_zip import write_examples_zip


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _zip_bytes(*pairs: tuple[str, str]) -> bytes:
    buf = BytesIO()
    with ZipFile(buf, "w") as zf:
        for name, text in pairs:
            zf.writestr(f"examples/{name}.toml", text)
    return buf.getvalue()


def test_release_tag_prefixes_installed_version(monkeypatch):
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    assert release_tag() == "v0.4.1"
    assert release_tag("0.4.1") == "v0.4.1"
    assert release_tag("v0.4.1") == "v0.4.1"


def test_release_tag_unknown_is_loud(monkeypatch):
    monkeypatch.setattr("parch.init.__version__", "unknown")
    with pytest.raises(FetchError, match="package version unknown"):
        release_tag()


def test_examples_zip_url_uses_installed_tag(monkeypatch):
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    assert examples_zip_url() == (
        f"https://github.com/yyolk/parch/releases/download/v0.4.1/{EXAMPLES_ZIP_NAME}"
    )


def test_fetch_examples_zip_returns_body(monkeypatch):
    body = _zip_bytes(("nomad", "year = 2026\n"))
    seen: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        seen["url"] = request.full_url
        seen["ua"] = request.get_header("User-agent")
        seen["timeout"] = timeout
        return _FakeResponse(body)

    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    assert fetch_examples_zip() == body
    assert seen["url"] == examples_zip_url()
    assert seen["ua"] == "parch"
    assert seen["timeout"] == 15


def test_fetch_examples_zip_urlerror_is_loud(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise URLError("Name or service not known")

    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    with pytest.raises(FetchError, match="need network for --from-release") as caught:
        fetch_examples_zip()
    assert "fetch failed" in str(caught.value)
    assert EXAMPLES_ZIP_NAME in str(caught.value)


def test_fetch_examples_zip_http_404_is_loud(monkeypatch):
    url = examples_zip_url("v0.4.1")

    def fake_urlopen(request, timeout=None):
        raise HTTPError(url, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    with pytest.raises(FetchError, match="missing on v0.4.1") as caught:
        fetch_examples_zip()
    assert "need network for --from-release" in str(caught.value)


def test_fetch_examples_zip_http_error_is_loud(monkeypatch):
    url = examples_zip_url("v0.4.1")

    def fake_urlopen(request, timeout=None):
        raise HTTPError(url, 500, "Boom", hdrs=None, fp=None)

    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    with pytest.raises(FetchError, match="HTTP 500"):
        fetch_examples_zip()


def test_fetch_examples_zip_timeout_is_loud(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    with pytest.raises(FetchError, match="timed out"):
        fetch_examples_zip()


def test_fetch_examples_zip_empty_body_is_loud(monkeypatch):
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", lambda *a, **k: _FakeResponse(b""))
    with pytest.raises(FetchError, match="empty body"):
        fetch_examples_zip()


def test_extract_starter_unknown_lists_available():
    data = _zip_bytes(("nomad", "year = 2026\n"), ("scribe", "year = 2026\n"))
    with pytest.raises(ConfigError, match="unknown starter 'bujo'") as caught:
        extract_starter(data, "bujo")
    assert "nomad" in str(caught.value)
    assert "scribe" in str(caught.value)


def test_write_starter_refuses_overwrite(tmp_path: Path):
    dest = tmp_path / "nomad.toml"
    dest.write_text("already here\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="refusing to overwrite"):
        write_starter(dest, "year = 2026\n")
    assert dest.read_text(encoding="utf-8") == "already here\n"


def test_cli_init_requires_from_release(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "init requires --from-release" in err
    assert "not in the wheel" in err
    assert not (tmp_path / "nomad.toml").exists()


def test_cli_init_from_release_writes_default_nomad(
    tmp_path: Path, capsys, monkeypatch
):
    body = _zip_bytes(("nomad", 'year = 2026\ndevice = "supernote-nomad"\n'))
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", lambda *a, **k: _FakeResponse(body))
    monkeypatch.chdir(tmp_path)
    assert main(["--from-release"]) == 0
    dest = tmp_path / "nomad.toml"
    assert dest.read_text(encoding="utf-8") == (
        'year = 2026\ndevice = "supernote-nomad"\n'
    )
    assert capsys.readouterr().out.strip() == "nomad.toml"
    assert DEFAULT_STARTER == "nomad"


def test_cli_init_from_release_chosen_starter(tmp_path: Path, monkeypatch):
    body = _zip_bytes(
        ("nomad", "year = 2026\n"),
        ("scribe", 'device = "kindle-scribe"\n'),
    )
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", lambda *a, **k: _FakeResponse(body))
    dest = tmp_path / "kindle.toml"
    assert main(["--from-release", "--starter", "scribe", "-o", str(dest)]) == 0
    assert dest.read_text(encoding="utf-8") == 'device = "kindle-scribe"\n'


def test_cli_init_from_release_lists_starters(tmp_path: Path, capsys, monkeypatch):
    body = _zip_bytes(("nomad", "year = 2026\n"), ("scribe", "year = 2026\n"))
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", lambda *a, **k: _FakeResponse(body))
    monkeypatch.chdir(tmp_path)
    assert main(["--from-release", "--list"]) == 0
    assert capsys.readouterr().out.splitlines() == ["nomad", "scribe"]
    assert not (tmp_path / "nomad.toml").exists()


def test_cli_init_from_release_offline_exits_2(tmp_path: Path, capsys, monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise URLError("Network is unreachable")

    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    dest = tmp_path / "nomad.toml"
    assert main(["--from-release", "-o", str(dest)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("parch: fetch failed:")
    assert "need network for --from-release" in err
    assert not dest.exists()


def test_cli_init_refuses_overwrite_without_network(
    tmp_path: Path, capsys, monkeypatch
):
    dest = tmp_path / "nomad.toml"
    dest.write_text("keep\n", encoding="utf-8")

    def boom(*args, **kwargs):
        raise AssertionError("urlopen must not run when dest exists")

    monkeypatch.setattr("parch.init.urlopen", boom)
    assert main(["--from-release", "-o", str(dest)]) == 2
    assert "refusing to overwrite" in capsys.readouterr().err
    assert dest.read_text(encoding="utf-8") == "keep\n"


def test_cli_init_unknown_starter_exits_2(tmp_path: Path, capsys, monkeypatch):
    body = _zip_bytes(("nomad", "year = 2026\n"))
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", lambda *a, **k: _FakeResponse(body))
    dest = tmp_path / "bujo.toml"
    assert main(["--from-release", "--starter", "bujo", "-o", str(dest)]) == 2
    assert "unknown starter 'bujo'" in capsys.readouterr().err
    assert not dest.exists()


def test_press_verb_dispatches_init(tmp_path: Path, monkeypatch):
    body = _zip_bytes(("nomad", "year = 2026\n"))
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", lambda *a, **k: _FakeResponse(body))
    dest = tmp_path / "from-press.toml"
    assert press_main(["init", "--from-release", "-o", str(dest)]) == 0
    assert dest.read_text(encoding="utf-8") == "year = 2026\n"


def test_init_from_release_round_trips_repo_examples(tmp_path: Path, monkeypatch):
    zip_path = tmp_path / EXAMPLES_ZIP_NAME
    write_examples_zip(zip_path)
    body = zip_path.read_bytes()
    monkeypatch.setattr("parch.init.__version__", "0.4.1")
    monkeypatch.setattr("parch.init.urlopen", lambda *a, **k: _FakeResponse(body))
    dest = tmp_path / "scribe.toml"
    assert main(["--from-release", "--starter", "scribe", "-o", str(dest)]) == 0
    assert dest.read_bytes() == Path("examples/scribe.toml").read_bytes()
