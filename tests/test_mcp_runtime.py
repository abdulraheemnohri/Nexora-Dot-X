import pytest
from nexora.mcp.runtime import MCPProcessConfig


def test_mcp_process_config_rejects_empty_command():
    from nexora.mcp.runtime import MCPStdioClient
    with pytest.raises(ValueError):
        MCPStdioClient(MCPProcessConfig([]))


def test_mcp_process_config_defaults():
    c = MCPProcessConfig(["python", "server.py"])
    assert c.timeout == 30.0
