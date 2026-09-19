"""parch init --fetch: pinned GitHub raw starter, loud offline failure."""

from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from parch import ConfigError, FetchError
from parch.init import STARTER_URL, fetch_starter, main, write_starter
from parch.press import main as press_main


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_starter_url_is_pinned_nomad_on_master():
    assert STARTER_URL == (
        "https://raw.githubusercontent.com/yyolk/parch/master/examples/nomad.toml"
    )


def test_fetch_starter_returns_body(monkeypatch):
    def fake_urlopen(request, timeout=None):
        assert request.full_url == STARTER_URL
        assert request.get_header("User-agent") == "parch"
        assert timeout == 15
        return _FakeResponse(b'year = 2026\ndevice = "supernote-nomad"\n')

    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    text = fetch_starter()
    assert "year = 2026" in text
    assert "supernote-nomad" in text


def test_fetch_starter_urlerror_is_loud(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise URLError("Name or service not known")

    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    with pytest.raises(FetchError, match="need network for --fetch") as caught:
        fetch_starter()
    assert STARTER_URL in str(caught.value)
    assert "fetch failed" in str(caught.value)


def test_fetch_starter_http_error_is_loud(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise HTTPError(STARTER_URL, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    with pytest.raises(FetchError, match="HTTP 404") as caught:
        fetch_starter()
    assert STARTER_URL in str(caught.value)


def test_fetch_starter_timeout_is_loud(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    with pytest.raises(FetchError, match="timed out"):
        fetch_starter()


def test_fetch_starter_empty_body_is_loud(monkeypatch):
    monkeypatch.setattr("parch.init.urlopen", lambda *a, **k: _FakeResponse(b"   \n"))
    with pytest.raises(FetchError, match="empty body"):
        fetch_starter()


def test_write_starter_refuses_overwrite(tmp_path: Path):
    dest = tmp_path / "nomad.toml"
    dest.write_text("already here\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="refusing to overwrite"):
        write_starter(dest, "year = 2026\n")
    assert dest.read_text(encoding="utf-8") == "already here\n"


def test_cli_init_requires_fetch(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "init requires --fetch" in err
    assert "not in the wheel" in err
    assert not (tmp_path / "nomad.toml").exists()


def test_cli_init_fetch_writes_dest(tmp_path: Path, capsys, monkeypatch):
    body = 'year = 2026\ndevice = "supernote-nomad"\n'

    monkeypatch.setattr(
        "parch.init.urlopen", lambda *a, **k: _FakeResponse(body.encode())
    )
    dest = tmp_path / "starter.toml"
    assert main(["--fetch", "-o", str(dest)]) == 0
    assert dest.read_text(encoding="utf-8") == body
    assert capsys.readouterr().out.strip() == str(dest)


def test_cli_init_fetch_offline_exits_2(tmp_path: Path, capsys, monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise URLError("Network is unreachable")

    monkeypatch.setattr("parch.init.urlopen", fake_urlopen)
    dest = tmp_path / "nomad.toml"
    assert main(["--fetch", "-o", str(dest)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("parch: fetch failed:")
    assert "need network for --fetch" in err
    assert not dest.exists()


def test_cli_init_refuses_overwrite_without_network(
    tmp_path: Path, capsys, monkeypatch
):
    dest = tmp_path / "nomad.toml"
    dest.write_text("keep\n", encoding="utf-8")

    def boom(*args, **kwargs):
        raise AssertionError("urlopen must not run when dest exists")

    monkeypatch.setattr("parch.init.urlopen", boom)
    assert main(["--fetch", "-o", str(dest)]) == 2
    assert "refusing to overwrite" in capsys.readouterr().err
    assert dest.read_text(encoding="utf-8") == "keep\n"


def test_press_verb_dispatches_init(tmp_path: Path, monkeypatch):
    body = "year = 2026\n"
    monkeypatch.setattr(
        "parch.init.urlopen", lambda *a, **k: _FakeResponse(body.encode())
    )
    dest = tmp_path / "from-press.toml"
    assert press_main(["init", "--fetch", "-o", str(dest)]) == 0
    assert dest.read_text(encoding="utf-8") == body
