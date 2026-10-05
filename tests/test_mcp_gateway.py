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
