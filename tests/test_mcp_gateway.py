from nexora.mcp.gateway import MCPGateway, MCPServer


def test_mcp_discovery_is_disabled_until_server_enabled():
    g = MCPGateway()
    g.register_server(MCPServer("demo", "Demo MCP"))
    ids = g.discover("demo", [{"name":"search","description":"Search"}])
    assert ids == ["mcp.demo.search"]
    assert not g.registry.get("mcp.demo.search").enabled


def test_mcp_allowlist_controls_tools():
    g = MCPGateway()
    g.register_server(MCPServer("demo", "Demo", enabled=True, allowed_tools={"search"}))
    g.discover("demo", [{"name":"search"},{"name":"write"}])
    assert g.registry.get("mcp.demo.search").enabled
    assert not g.registry.get("mcp.demo.write").enabled


def test_enabled_server_is_allowlisted_for_mcp_policy():
    g = MCPGateway()
    g.register_server(MCPServer("demo", "Demo", enabled=True, trusted=True))
    result = g.policy.evaluate("demo", "search")
    assert result.decision.value == "ALLOW"


import pytest

@pytest.mark.asyncio
async def test_disconnect_disables_registered_mcp_tools():
    g = MCPGateway()
    g.register_server(MCPServer("demo", "Demo", enabled=True, trusted=True))
    g.discover("demo", [{"name": "search"}])
    g.bind_handler("mcp.demo.search", lambda args: {"ok": True, "output": "x"})
    await g.disconnect("demo")
    assert not g.registry.get("mcp.demo.search").enabled
    assert "mcp.demo.search" not in g.handlers
