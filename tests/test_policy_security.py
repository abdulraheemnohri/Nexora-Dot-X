from nexora.control.policy import Decision, PolicyEngine


def test_dangerous_commands_are_blocked_before_grants():
    policy = PolicyEngine()
    policy.allowed_always.add(("terminal", "rm -rf /"))
    result = policy.evaluate("terminal", "rm -rf /")
    assert result.decision is Decision.BLOCK


def test_unknown_actions_require_approval():
    result = PolicyEngine().evaluate("terminal", "python script.py")
    assert result.decision is Decision.ASK
