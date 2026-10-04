from nexora.control.approvals import ApprovalCenter
from nexora.control.policy import PolicyEngine, Decision
from nexora.core.executor import Executor

from nexora.database.engine import init_db


def test_always_allow_grant(tmp_path):
    init_db(tmp_path / "test.db")
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


def test_always_allow_does_not_leak_to_other_actions(tmp_path):
    init_db(tmp_path / "test.db")
    center = ApprovalCenter()
    a = center.request("terminal", "git push origin main", "test", "high")
    center.approve(a.id, always=True)
    ex = Executor()
    other = ex.policy.evaluate("terminal", "git push origin other-branch")
    assert other.decision is Decision.ASK


def test_dangerous_never_auto_allowed(tmp_path):
    init_db(tmp_path / "test.db")
    ex = Executor()
    # even "always" cannot whitelisted dangerous commands
    from nexora.control.approvals import _policy
    _policy.allowed_always.add(("terminal", "rm -rf /"))
    decision = ex.policy.evaluate("terminal", "rm -rf /")
    assert decision.decision is Decision.BLOCK
