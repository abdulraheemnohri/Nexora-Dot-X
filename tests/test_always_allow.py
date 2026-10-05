from nexora.control.approvals import ApprovalCenter
from nexora.control.policy import Decision, ALWAYS_ALLOWED
from nexora.control import always_allow
from nexora.core.executor import Executor

from nexora.database.engine import init_db


def test_always_allow_grant(tmp_path):
    init_db(tmp_path / "test.db")
    ALWAYS_ALLOWED.clear()
    center = ApprovalCenter()
    a = center.request("terminal", "pip install requests", "test", "high")
    center.approve(a.id, always=True)
    # a fresh executor now auto-allows the exact same normalized action
    ex = Executor()
    decision = ex.policy.evaluate("terminal", "pip  install   requests")
    assert decision.decision is Decision.ALLOW
    out = ex.execute({"tool": "terminal", "action": "pip install requests"},
                     dry_run=True)
    assert out.ok is True
    ALWAYS_ALLOWED.clear()


def test_always_allow_does_not_leak_to_other_actions(tmp_path):
    init_db(tmp_path / "test.db")
    ALWAYS_ALLOWED.clear()
    center = ApprovalCenter()
    a = center.request("terminal", "git push origin main", "test", "high")
    center.approve(a.id, always=True)
    ex = Executor()
    other = ex.policy.evaluate("terminal", "git push origin other-branch")
    assert other.decision is Decision.ASK
    ALWAYS_ALLOWED.clear()


def test_dangerous_never_auto_allowed(tmp_path):
    init_db(tmp_path / "test.db")
    ALWAYS_ALLOWED.clear()
    ex = Executor()
    # even "always" cannot whitelisted dangerous commands
    ALWAYS_ALLOWED.add(("terminal", "rm -rf /"))
    decision = ex.policy.evaluate("terminal", "rm -rf /")
    assert decision.decision is Decision.BLOCK
    ALWAYS_ALLOWED.clear()


def test_always_allow_survives_restart(tmp_path):
    init_db(tmp_path / "test.db")
    ALWAYS_ALLOWED.clear()
    center = ApprovalCenter()
    a = center.request("terminal", "pip install requests", "test", "high")
    center.approve(a.id, always=True)
    assert ("terminal", "pip install requests") in always_allow.list_grants()

    # simulate a process restart: fresh in-memory state, reload from SQLite
    ALWAYS_ALLOWED.clear()
    assert ("terminal", "pip install requests") not in ALWAYS_ALLOWED
    always_allow.load_grants()
    assert ("terminal", "pip install requests") in ALWAYS_ALLOWED
    ex = Executor()
    decision = ex.policy.evaluate("terminal", "pip install requests")
    assert decision.decision is Decision.ALLOW
    ALWAYS_ALLOWED.clear()


def test_revoke_grant(tmp_path):
    init_db(tmp_path / "test.db")
    ALWAYS_ALLOWED.clear()
    always_allow.save_grant("terminal", "git push origin main")
    assert ("terminal", "git push origin main") in ALWAYS_ALLOWED
    assert always_allow.revoke_grant("terminal", "git push origin main") is True
    assert ("terminal", "git push origin main") not in ALWAYS_ALLOWED
    assert always_allow.revoke_grant("terminal", "git push origin main") is False
    ALWAYS_ALLOWED.clear()


def test_save_grant_normalizes_whitespace(tmp_path):
    init_db(tmp_path / "test.db")
    ALWAYS_ALLOWED.clear()
    always_allow.save_grant("terminal", "git   push    origin main")
    assert ("terminal", "git push origin main") in ALWAYS_ALLOWED
    grants = always_allow.list_grants()
    assert ("terminal", "git push origin main") in grants
    ALWAYS_ALLOWED.clear()
