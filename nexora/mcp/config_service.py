"""Persistent MCP server configuration service."""
import json
from nexora.database.models import MCPServerConfig
from nexora.database import repositories as repo
from nexora.mcp.gateway import MCPServer

class MCPConfigService:
    def list(self):
        return repo.get_all(MCPServerConfig, limit=1000, order_desc="created_at")

    def save(self, server_id: str, name: str, command: list[str], cwd: str = "",
             enabled: bool = False, trusted: bool = False,
             allowed_tools: list[str] | None = None):
        existing = repo.get_by_id(MCPServerConfig, server_id)
        values = dict(name=name, command_json=json.dumps(command),
                      cwd=cwd, enabled=enabled, trusted=trusted,
                      allowed_tools_json=json.dumps(allowed_tools or []))
        if existing:
            return repo.update_fields(existing, **values)
        return repo.add_obj(MCPServerConfig(id=server_id, **values))

    def delete(self, server_id: str):
        existing = repo.get_by_id(MCPServerConfig, server_id)
        if existing is None:
            return False
        repo.delete_obj(existing)
        return True

    def to_server(self, row):
        return MCPServer(
            id=row.id, name=row.name, enabled=row.enabled, trusted=row.trusted,
            allowed_tools=set(json.loads(row.allowed_tools_json or "[]")),
            metadata={"command": json.loads(row.command_json or "[]"), "cwd": row.cwd or ""},
        )
