"""Tests for the approved-skill execution runtime."""
from pathlib import Path

from nexora.skills.runtime import run_skill


def _make_skill(tmp_path: Path, name: str, source: str) -> dict:
    d = tmp_path / name
    (d / "tools").mkdir(parents=True, exist_ok=True)
    (d / "tools" / "main.py").write_text(source, encoding="utf-8")
    return {"name": name, "_dir": str(d), "_status": "active"}


def test_run_skill_ok(tmp_path):
    skill = _make_skill(tmp_path, "echoer",
                        "def run(payload):\n"
                        "    return 'echo: ' + str(payload)\n")
    r = run_skill(skill, "hi")
    assert r["ok"]
    assert r["result"] == "echo: hi"


def test_run_skill_pending_blocked(tmp_path):
    skill = _make_skill(tmp_path, "pending_one", "def run(p):\n    return p\n")
    skill["_status"] = "pending"
    r = run_skill(skill)
    assert not r["ok"]
    assert "not approved" in r["error"]


def test_run_skill_scan_blocked(tmp_path):
    skill = _make_skill(tmp_path, "bad",
                        "import subprocess\n\n\ndef run(p):\n    return p\n")
    r = run_skill(skill)
    assert not r["ok"]
    assert "static scan failed" in r["error"]


def test_run_skill_no_main(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    r = run_skill({"name": "empty", "_dir": str(d), "_status": "active"})
    assert not r["ok"]
    assert "main.py" in r["error"]


def test_run_skill_no_run_function(tmp_path):
    skill = _make_skill(tmp_path, "norun", "def helper():\n    return 1\n")
    r = run_skill(skill)
    assert not r["ok"]
    assert "run()" in r["error"]
