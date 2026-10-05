"""Tests for the skill static safety scanner."""
from pathlib import Path

from nexora.skills.scanner import scan_skill_files, scan_source


def test_scan_source_clean():
    src = "import json\n\n\ndef hi(name):\n    return 'hi ' + name\n"
    r = scan_source(src)
    assert r["ok"]
    assert r["issues"] == []


def test_scan_source_flags_forbidden():
    src = "import subprocess\n\n\ndef go():\n    eval('1')\n"
    r = scan_source(src)
    assert not r["ok"]
    assert any("subprocess" in i for i in r["issues"])
    assert any("eval" in i for i in r["issues"])


def test_scan_source_flags_network():
    r = scan_source("import urllib\n")
    assert not r["ok"]
    assert any("network" in i for i in r["issues"])


def test_scan_source_syntax_error():
    r = scan_source("def broken(:\n")
    assert not r["ok"]
    assert any("syntax error" in i for i in r["issues"])


def test_scan_skill_files(tmp_path: Path):
    d = tmp_path / "my_skill"
    (d / "tools").mkdir(parents=True)
    (d / "tools" / "main.py").write_text("import socket\n", encoding="utf-8")
    (d / "skill.json").write_text("{}", encoding="utf-8")
    r = scan_skill_files({"_dir": str(d)})
    assert r["files_scanned"] == 1
    assert not r["ok"]
    assert any("socket" in i for i in r["issues"])


def test_scan_skill_files_missing_dir():
    r = scan_skill_files({"_dir": "/nonexistent/skill-x"})
    assert r["ok"]
    assert r["files_scanned"] == 0
    assert r["issues"] == []
