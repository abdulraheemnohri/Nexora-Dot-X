"""Tests for the litert-lm CLI bridge (pure arg building, no subprocess)."""
import pytest

from nexora.models.litert import cli_bridge as cb


def test_resolve_cli_prefers_direct_binary(monkeypatch):
    monkeypatch.setattr(cb.shutil, "which", lambda name:
                        "/usr/bin/litert-lm" if name == "litert-lm" else None)
    assert cb.resolve_cli() == ["litert-lm"]


def test_resolve_cli_falls_back_to_uvx(monkeypatch):
    monkeypatch.setattr(cb.shutil, "which", lambda name:
                        "/usr/bin/uvx" if name == "uvx" else None)
    assert cb.resolve_cli() == ["uvx", "litert-lm"]


def test_resolve_cli_missing(monkeypatch):
    monkeypatch.setattr(cb.shutil, "which", lambda name: None)
    assert cb.resolve_cli() is None


def test_build_import_args():
    assert cb.build_import_args("org/repo", "model.litertlm", "my-model") == [
        "import", "--from-huggingface-repo=org/repo", "model.litertlm", "my-model"]


def test_build_serve_args_defaults():
    assert cb.build_serve_args() == ["serve", "--host=127.0.0.1", "--port=9379"]


def test_build_serve_args_custom():
    args = cb.build_serve_args(host="0.0.0.0", port=8080, verbose=True)
    assert args == ["serve", "--host=0.0.0.0", "--port=8080", "--verbose"]


def test_build_run_args_local():
    assert cb.build_run_args("/models/m.litertlm", prompt="hi") == [
        "run", "/models/m.litertlm", "--prompt=hi"]


def test_build_run_args_remote_and_options():
    args = cb.build_run_args("m.litertlm", prompt="hi", backend="gpu",
                             speculative=True, attachment="img.jpg",
                             vision_backend="gpu",
                             from_repo="litert-community/gemma-4-E2B-it-litert-lm")
    assert args == [
        "run", "--from-huggingface-repo=litert-community/gemma-4-E2B-it-litert-lm",
        "m.litertlm", "--backend=gpu", "--enable-speculative-decoding=true",
        "--vision-backend=gpu", "--attachment=img.jpg", "--prompt=hi"]


def test_build_run_args_no_prompt():
    assert cb.build_run_args("m.litertlm") == ["run", "m.litertlm"]


def test_require_network_blocks_by_default(monkeypatch):
    monkeypatch.setenv("NEXORA_LOCAL_ONLY", "true")
    with pytest.raises(PermissionError):
        cb.require_network(False)


def test_require_network_allows(monkeypatch):
    monkeypatch.setenv("NEXORA_LOCAL_ONLY", "true")
    cb.require_network(True)  # explicit user consent


def test_require_network_env_allows(monkeypatch):
    monkeypatch.setenv("NEXORA_LOCAL_ONLY", "false")
    cb.require_network(False)


def test_spawn_serve_returns_none_without_cli(monkeypatch):
    monkeypatch.setattr(cb, "resolve_cli", lambda: None)
    assert cb.spawn_serve(["serve", "--port=9379"]) is None


def test_spawn_serve_returns_popen(monkeypatch):
    class FakeProc:
        pid = 4242

    def fake_popen(cmd, **kwargs):
        fake_popen.last_cmd = cmd
        return FakeProc()

    fake_popen.last_cmd = None
    monkeypatch.setattr(cb, "resolve_cli", lambda: ["litert-lm"])
    monkeypatch.setattr(cb.subprocess, "Popen", fake_popen)
    proc = cb.spawn_serve(["serve", "--host=127.0.0.1", "--port=9379"])
    assert isinstance(proc, FakeProc)
    assert fake_popen.last_cmd == ["litert-lm", "serve",
                                   "--host=127.0.0.1", "--port=9379"]
