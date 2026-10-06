from nexora.control.policy import Decision
from nexora.mcp.policy import MCPPolicy


def test_mcp_unallowlisted_server_is_blocked():
    result = MCPPolicy(allowed_servers=set()).evaluate("demo", "search")
    assert result.decision is Decision.BLOCK


def test_mcp_untrusted_allowlisted_tool_requires_approval():
    result = MCPPolicy(allowed_servers={"demo"}).evaluate("demo", "search")
    assert result.decision is Decision.ASK


def test_mcp_trusted_server_is_allowed():
    result = MCPPolicy(allowed_servers={"demo"}, trusted_servers={"demo"}).evaluate("demo", "search")
    assert result.decision is Decision.ALLOW
