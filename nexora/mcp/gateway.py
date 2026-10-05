"""System-1 controlled MCP registry/gateway."""
from dataclasses import dataclass, field
from typing import Any, Callable
from nexora.tools.registry import ToolRegistry, ToolSpec
from nexora.mcp.runtime import MCPStdioClient, MCPProcessConfig

@dataclass
class MCPServer:
    id: str
    name: str
    enabled: bool = False
    trusted: bool = False
    allowed_tools: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

class MCPGateway:
    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()
        self.servers: dict[str, MCPServer] = {}
        self.handlers: dict[str, Callable] = {}

    def register_server(self, server: MCPServer):
        self.servers[server.id] = server
        return server

    def set_enabled(self, server_id: str, enabled: bool):
        server = self.servers[server_id]
        server.enabled = enabled
        return server

    def discover(self, server_id: str, tools: list[dict[str, Any]]):
        server = self.servers[server_id]
        found = []
        for item in tools:
            name = str(item.get("name", "")).strip()
            if not name: continue
            tool_id = f"mcp.{server_id}.{name}"
            spec = ToolSpec(id=tool_id, name=name,
                description=str(item.get("description", "MCP tool")),
                risk=str(item.get("risk", "high")),
                enabled=server.enabled and (not server.allowed_tools or name in server.allowed_tools),
                input_schema=item.get("inputSchema") or item.get("input_schema") or {"type":"object","properties":{},"additionalProperties":False},
                permissions=[f"mcp:{server_id}"], tags=["mcp", server_id])
            self.registry.register(spec)
            found.append(tool_id)
        return found

    def bind_handler(self, tool_id: str, handler: Callable):
        self.handlers[tool_id] = handler
        self.registry._handlers[tool_id] = handler

    def schemas(self): return self.registry.schemas()
    def servers_list(self): return list(self.servers.values())

    async def connect_stdio(self, server_id: str, config: MCPProcessConfig):
        server = self.servers[server_id]
        client = MCPStdioClient(config)
        await client.start()
        tools = await client.list_tools()
        self.discover(server_id, tools)
        self.handlers.update({f"mcp.{server_id}.{t['name']}": (lambda args, c=client, n=t['name']: __import__('asyncio').run(c.call_tool(n, args))) for t in tools if t.get('name')})
        for tool_id, handler in list(self.handlers.items()):
            if tool_id.startswith(f"mcp.{server_id}."):
                self.bind_handler(tool_id, handler)
        server.metadata['transport'] = 'stdio'
        server.metadata['client'] = client
        return tools

    async def disconnect(self, server_id: str):
        server = self.servers[server_id]
        client = server.metadata.pop('client', None)
        if client:
            await client.close()
