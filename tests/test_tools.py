from pathlib import Path
from nexora.database.engine import init_db
from nexora.tools.registry import ToolRegistry
from nexora.tools import terminal as terminal_tool
from nexora.tools import filesystem as fs_tool
from nexora.tools import http as http_tool


def test_terminal_blocked(tmp_path: Path):
    init_db(tmp_path / "test.db")
    r = ToolRegistry()
    terminal_tool.register(r)
    out = r.run("terminal", "rm -rf /")
    assert out["ok"] is False
    assert "BLOCKED" in out["output"]


def test_terminal_safe(tmp_path: Path):
    init_db(tmp_path / "test.db")
    r = ToolRegistry()
    terminal_tool.register(r)
    out = r.run("terminal", "git status")
    assert out["ok"] is True or "APPROVAL" in out["output"]


def test_filesystem_sandbox(tmp_path: Path, monkeypatch):
    import nexora.tools.filesystem as f
    monkeypatch.setattr(f, "ALLOWED_ROOTS", [tmp_path])
    tool = f.FilesystemTool()
    p = tmp_path / "note.txt"
    p.write_text("hello")
    assert "hello" in tool.run(f"read:{p}")


def test_http_disabled_local_only(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("NEXORA_LOCAL_ONLY", "true")
    import importlib
    import nexora.config as cfg
    importlib.reload(cfg)
    import nexora.tools.http as h
    importlib.reload(h)
    r = ToolRegistry()
    h.register(r)
    out = r.run("http", "https://example.com")
    assert out["ok"] is False
