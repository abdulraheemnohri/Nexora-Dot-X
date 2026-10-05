from nexora.control.policy import Decision, PolicyEngine


def test_dangerous_commands_are_blocked_before_grants():
    policy = PolicyEngine()
    policy.allowed_always.add(("terminal", "rm -rf /"))
    result = policy.evaluate("terminal", "rm -rf /")
    assert result.decision is Decision.BLOCK


def test_unknown_actions_require_approval():
    result = PolicyEngine().evaluate("terminal", "python script.py")
    assert result.decision is Decision.ASK


def test_approval_claim_is_single_use():
    from nexora.core import executor as executor_module

    class FakeApproval:
        id = "approval-1"
        tool = "test"
        action = "do-it"
        status = "approved"

    class FakeRepo:
        def __init__(self):
            self.claims = 0

        def get_by_id(self, model, approval_id):
            return FakeApproval()

        def claim_approval(self, model, approval_id):
            self.claims += 1
            if self.claims == 1:
                return FakeApproval()
            return None

    class FakeTools:
        def run(self, tool, action):
            return {"ok": True, "output": "done"}

    original_repo = executor_module.repo
    executor_module.repo = FakeRepo()
    try:
        runner = executor_module.Executor(FakeTools())
        assert runner.resume("approval-1").ok
        assert not runner.resume("approval-1").ok
    finally:
        executor_module.repo = original_repo
