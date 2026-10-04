from nexora.skills.manager import SkillManager


def test_submit_requires_approval(tmp_path):
    mgr = SkillManager(skills_dir=tmp_path / "skills")
    r = mgr.submit("daily-news", {"description": "news digest"},
                   {"main.py": "print('hi')"})
    assert r["ok"] is True and r["status"] == "pending"
    assert mgr.scan() == []                    # not active yet
    assert len(mgr.pending()) == 1


def test_approve_activates_skill(tmp_path):
    mgr = SkillManager(skills_dir=tmp_path / "skills")
    mgr.submit("daily-news", {"description": "d"}, {"main.py": "print(1)"})
    r = mgr.approve("daily-news")
    assert r["ok"] is True
    active = [s["name"] for s in mgr.scan()]
    assert active == ["daily-news"]
    assert mgr.pending() == []


def test_reject_removes_skill(tmp_path):
    mgr = SkillManager(skills_dir=tmp_path / "skills")
    mgr.submit("bad", {"description": "b"}, {"main.py": "print(1)"})
    r = mgr.reject("bad")
    assert r["ok"] is True
    assert mgr.scan() == [] and mgr.pending() == []
    assert mgr.reject("bad")["ok"] is False


def test_invalid_name_rejected(tmp_path):
    mgr = SkillManager(skills_dir=tmp_path / "skills")
    assert mgr.submit("../evil", {}, {})["ok"] is False
    assert mgr.submit(".hidden", {}, {})["ok"] is False
