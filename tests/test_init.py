"""parch init --template: thin copier wrapper, optional extra, public pin."""

from pathlib import Path

import pytest

from parch import ConfigError, TemplateError
from parch.init import (
    DEFAULT_PUBLIC_TEMPLATE,
    STARTER_DIR,
    apply_template,
    checkout_root,
    load_copier,
    main,
    resolve_template_src,
)
from parch.press import main as press_main


class _FakeCopier:
    def __init__(self, *, fail: Exception | None = None):
        self.fail = fail
        self.calls: list[dict[str, object]] = []

    def run_copy(self, src_path, dst_path, **kwargs):
        self.calls.append({"src": src_path, "dst": dst_path, **kwargs})
        if self.fail is not None:
            raise self.fail
        dest = Path(dst_path)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "parch.toml").write_text('year = 2026\ndevice = "supernote-nomad"\n')


def test_public_pin_is_this_repo():
    assert DEFAULT_PUBLIC_TEMPLATE == "gh:yyolk/parch"
    root = Path(__file__).resolve().parents[1]
    assert (root / "copier.yml").is_file()
    assert "_subdirectory: templates/starter" in (root / "copier.yml").read_text(
        encoding="utf-8"
    )
    assert (root / STARTER_DIR / "parch.toml.jinja").is_file()


def test_checkout_root_finds_repo():
    root = checkout_root()
    assert root is not None
    assert (root / "copier.yml").is_file()
    assert (root / STARTER_DIR).is_dir()


def test_resolve_template_src_prefers_explicit():
    assert resolve_template_src("gh:other/repo") == "gh:other/repo"
    assert resolve_template_src("/tmp/tpl") == "/tmp/tpl"


def test_resolve_template_src_defaults_to_checkout():
    assert resolve_template_src(None) == str(checkout_root())


def test_resolve_template_src_falls_back_to_public_pin(monkeypatch):
    monkeypatch.setattr("parch.init.checkout_root", lambda: None)
    assert resolve_template_src(None) == DEFAULT_PUBLIC_TEMPLATE


def test_load_copier_missing_extra_is_loud(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "copier" or name.startswith("copier."):
            raise ImportError("No module named copier")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(TemplateError, match="template extra"):
        load_copier()


def test_apply_template_invokes_copier(tmp_path: Path, monkeypatch):
    fake = _FakeCopier()
    monkeypatch.setattr("parch.init.load_copier", lambda: fake)
    dest = tmp_path / "book"
    assert apply_template("gh:yyolk/parch", dest) == dest
    assert dest.joinpath("parch.toml").is_file()
    assert fake.calls[0]["src"] == "gh:yyolk/parch"
    assert Path(str(fake.calls[0]["dst"])) == dest
    assert fake.calls[0]["defaults"] is True
    assert fake.calls[0]["overwrite"] is False
    assert fake.calls[0]["quiet"] is True
    assert "vcs_ref" not in fake.calls[0]


def test_apply_template_local_git_uses_head(tmp_path: Path, monkeypatch):
    fake = _FakeCopier()
    monkeypatch.setattr("parch.init.load_copier", lambda: fake)
    src = tmp_path / "repo"
    src.mkdir()
    (src / ".git").mkdir()
    dest = tmp_path / "book"
    apply_template(str(src), dest)
    assert fake.calls[0]["vcs_ref"] == "HEAD"


def test_apply_template_refuses_nonempty_dest(tmp_path: Path, monkeypatch):
    dest = tmp_path / "book"
    dest.mkdir()
    (dest / "keep.toml").write_text("keep\n", encoding="utf-8")

    def boom():
        raise AssertionError("copier must not run when dest exists")

    monkeypatch.setattr("parch.init.load_copier", boom)
    with pytest.raises(ConfigError, match="refusing to overwrite"):
        apply_template("gh:yyolk/parch", dest)
    assert (dest / "keep.toml").read_text(encoding="utf-8") == "keep\n"


def test_apply_template_wraps_copier_failure(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "parch.init.load_copier",
        lambda: _FakeCopier(fail=RuntimeError("clone failed")),
    )
    with pytest.raises(TemplateError, match="copier failed: clone failed"):
        apply_template("gh:yyolk/parch", tmp_path / "empty")


def test_cli_init_requires_template(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "init requires --template" in err
    assert "parch[template]" in err
    assert not (tmp_path / "parch-starter").exists()


def test_cli_init_template_writes_dest(tmp_path: Path, capsys, monkeypatch):
    fake = _FakeCopier()
    monkeypatch.setattr("parch.init.load_copier", lambda: fake)
    dest = tmp_path / "out"
    assert main(["--template", "gh:yyolk/parch", "-o", str(dest)]) == 0
    assert dest.joinpath("parch.toml").is_file()
    assert capsys.readouterr().out.strip() == str(dest)
    assert fake.calls[0]["src"] == "gh:yyolk/parch"


def test_cli_init_passes_vcs_ref(tmp_path: Path, monkeypatch):
    fake = _FakeCopier()
    monkeypatch.setattr("parch.init.load_copier", lambda: fake)
    dest = tmp_path / "out"
    assert (
        main(["--template", "gh:yyolk/parch", "-o", str(dest), "--vcs-ref", "master"])
        == 0
    )
    assert fake.calls[0]["vcs_ref"] == "master"


def test_cli_init_template_default_src_is_checkout(tmp_path: Path, capsys, monkeypatch):
    fake = _FakeCopier()
    monkeypatch.setattr("parch.init.load_copier", lambda: fake)
    dest = tmp_path / "book"
    assert main(["--template", "-o", str(dest)]) == 0
    assert fake.calls[0]["src"] == str(checkout_root())
    assert capsys.readouterr().out.strip() == str(dest)


def test_cli_init_missing_extra_exits_2(tmp_path: Path, capsys, monkeypatch):
    def boom():
        raise TemplateError(
            "init --template needs the template extra "
            "(pip install 'parch[template]' or uv sync --extra template)"
        )

    monkeypatch.setattr("parch.init.load_copier", boom)
    dest = tmp_path / "book"
    assert main(["--template", "gh:yyolk/parch", "-o", str(dest)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("parch: init --template needs the template extra")
    assert not dest.exists() or not any(dest.iterdir())


def test_cli_init_refuses_overwrite(tmp_path: Path, capsys, monkeypatch):
    dest = tmp_path / "book"
    dest.mkdir()
    (dest / "keep.toml").write_text("keep\n", encoding="utf-8")

    def boom():
        raise AssertionError("copier must not run when dest exists")

    monkeypatch.setattr("parch.init.load_copier", boom)
    assert main(["--template", "gh:yyolk/parch", "-o", str(dest)]) == 2
    assert "refusing to overwrite" in capsys.readouterr().err
    assert (dest / "keep.toml").read_text(encoding="utf-8") == "keep\n"


def test_press_verb_dispatches_init(tmp_path: Path, monkeypatch):
    fake = _FakeCopier()
    monkeypatch.setattr("parch.init.load_copier", lambda: fake)
    dest = tmp_path / "from-press"
    assert press_main(["init", "--template", "gh:yyolk/parch", "-o", str(dest)]) == 0
    assert dest.joinpath("parch.toml").is_file()


@pytest.mark.parametrize(
    "starter",
    ["nomad", "scribe", "extras", "bujo", "projects", "engineering", "steno"],
)
def test_jinja_template_mentions_every_starter(starter: str):
    text = (
        Path(__file__).resolve().parents[1] / STARTER_DIR / "parch.toml.jinja"
    ).read_text(encoding="utf-8")
    assert f"starter == '{starter}'" in text


def test_copier_choices_are_label_to_value():
    text = (Path(__file__).resolve().parents[1] / "copier.yml").read_text(
        encoding="utf-8"
    )
    assert "Nomad year planner: nomad" in text
    assert "SuperNote Nomad: supernote-nomad" in text


@pytest.mark.parametrize(
    ("starter", "book", "device"),
    [
        ("nomad", "year-planner", "supernote-nomad"),
        ("scribe", "year-planner", "kindle-scribe"),
        ("extras", "year-planner", "supernote-nomad"),
        ("bujo", "bullet-journal", "supernote-nomad"),
        ("projects", "projects-notebook", "supernote-nomad"),
        ("engineering", "engineering-notebook", "supernote-nomad"),
        ("steno", "year-planner", "supernote-nomad"),
    ],
)
def test_apply_template_live_copier(
    tmp_path: Path, starter: str, book: str, device: str
):
    pytest.importorskip("copier")
    root = checkout_root()
    assert root is not None
    dest = tmp_path / starter
    apply_template(str(root), dest, data={"starter": starter})
    spec_path = dest / "parch.toml"
    assert spec_path.is_file()
    from parch.spec import Spec

    spec = Spec.from_path(spec_path)
    assert spec.year == 2026
    assert spec.device == device
    assert spec.book == book
    if starter == "steno":
        assert spec.steno_sheets == 1
    if starter == "extras":
        assert spec.favorites_pages == 1
        assert spec.my_100 is True
        assert spec.checkoff_365 is True
