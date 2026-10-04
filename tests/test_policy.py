from nexora.control.policy import PolicyEngine, Decision


def test_safe_command_allowed():
    r = PolicyEngine().evaluate("terminal", "ls")
    assert r.decision is Decision.ALLOW


def test_git_status_allowed():
    r = PolicyEngine().evaluate("terminal", "git status")
    assert r.decision is Decision.ALLOW


def test_dangerous_command_blocked():
    r = PolicyEngine().evaluate("terminal", "rm -rf /")
    assert r.decision is Decision.BLOCK


def test_unknown_command_requires_approval():
    r = PolicyEngine().evaluate("terminal", "somebrandnewcommand --flag")
    assert r.decision is Decision.ASK


def test_readonly_tool_allowed():
    r = PolicyEngine().evaluate("filesystem.read", "anything")
    assert r.decision is Decision.ALLOW
