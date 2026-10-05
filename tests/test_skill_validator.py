from pathlib import Path
import json
from nexora.skills.validator import validate_metadata, validate_skill_dir

def test_skill_metadata_validation():
    assert validate_metadata({
        "name": "research",
        "version": "1.0.0",
        "description": "Research",
        "entrypoint": "tools/main.py",
        "risk": "medium",
        "permissions": [],
    })["ok"]

def test_skill_rejects_path_escape():
    r = validate_metadata({
        "name": "bad_skill",
        "version": "1",
        "description": "bad",
        "entrypoint": "../main.py",
        "risk": "safe",
    })
    assert not r["ok"]

def test_skill_dir_requires_entrypoint(tmp_path: Path):
    d = tmp_path / "skill"
    d.mkdir()
    (d / "skill.json").write_text(json.dumps({
        "name": "demo_skill", "version": "1", "description": "demo",
        "entrypoint": "tools/main.py", "risk": "safe"
    }))
    assert not validate_skill_dir(d)["ok"]
