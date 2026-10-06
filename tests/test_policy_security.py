from nexora.control.policy import Decision, PolicyEngine


def test_dangerous_commands_are_blocked_before_grants():
    policy = PolicyEngine()
    policy.allowed_always.add(("terminal", "rm -rf /"))
    result = policy.evaluate("terminal", "rm -rf /")
    assert result.decision is Decision.BLOCK


def test_unknown_actions_require_approval():
    result = PolicyEngine().evaluate("terminal", "python script.py")
    assert result.decision is Decision.ASK


def test_approval_claim_is_single_use(monkeypatch):
    from nexora.core import executor as executor_module

    class FakeApproval:
        id = "approval-1"
        tool = "test"
        action = "do-it"
        status = "approved"

    calls = {"claim": 0}

    monkeypatch.setattr(
        executor_module.repo, "get_by_id",
        lambda model, approval_id: FakeApproval(),
    )

    def claim(approval_id):
        calls["claim"] += 1
        return FakeApproval() if calls["claim"] == 1 else None

    runner = executor_module.Executor(
        type("FakeTools", (), {"run": lambda self, tool, action: {"ok": True, "output": "done"}})()
    )
    monkeypatch.setattr(runner.approvals, "claim", claim)
    monkeypatch.setattr(runner.approvals, "mark_executed", lambda approval_id: FakeApproval())

    assert runner.resume("approval-1").ok
    assert not runner.resume("approval-1").ok
