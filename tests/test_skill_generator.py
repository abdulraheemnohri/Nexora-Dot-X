from pathlib import Path
from nexora.database.engine import init_db
from nexora.skills.generator import SkillGenerator
from nexora.skills.scanner import scan_source


def test_scanner_rejects_dangerous():
    r = scan_source("import subprocess\nsubprocess.run(['ls'])\n")
    assert r["ok"] is False


def test_scanner_accepts_pure_code():
    r = scan_source("def add(a, b):\n    return a + b\n")
    assert r["ok"] is True


def test_proposal_then_activation(tmp_path: Path):
    init_db(tmp_path / "test.db")
    g = SkillGenerator(skills_dir=tmp_path)
    p = g.propose("helper", "safe helper", "def run(x):\n    return x * 2\n")
    assert p.status == "PROPOSED"
    r = g.activate(p)
    assert r["ok"] is True
    assert (tmp_path / "helper" / "skill.json").exists()
