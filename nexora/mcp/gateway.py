"""System-1 controlled MCP registry/gateway."""
from dataclasses import dataclass, field
from typing import Any, Callable
from nexora.tools.registry import ToolRegistry, ToolSpec
from nexora.mcp.runtime import MCPStdioClient, MCPProcessConfig
from nexora.mcp.policy import MCPPolicy

@dataclass
class MCPServer:
    id: str
    name: str
    enabled: bool = False
    trusted: bool = False
    allowed_tools: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

class MCPGateway:
    def __init__(self, registry: ToolRegistry | None = None, policy: MCPPolicy | None = None):
        self.registry = registry or ToolRegistry()
        self.policy = policy or MCPPolicy()
        self.servers: dict[str, MCPServer] = {}
        self.handlers: dict[str, Callable] = {}

    def register_server(self, server: MCPServer):
        self.servers[server.id] = server
        if server.enabled:
            self.policy.allowed_servers.add(server.id)
        if server.trusted:
            self.policy.trusted_servers.add(server.id)
        return server

    def set_enabled(self, server_id: str, enabled: bool):
        server = self.servers[server_id]
        server.enabled = enabled
        if enabled:
            self.policy.allowed_servers.add(server_id)
        else:
            self.policy.allowed_servers.discard(server_id)
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
        self.registry.bind(tool_id, handler=handler)

    def schemas(self): return self.registry.schemas()
    def servers_list(self): return list(self.servers.values())

    async def connect_stdio(self, server_id: str, config: MCPProcessConfig):
        server = self.servers[server_id]
        client = MCPStdioClient(config)
        await client.start()
        tools = await client.list_tools()
        self.discover(server_id, tools)
        for t in tools:
            name = str(t.get('name', '')).strip()
            if not name:
                continue
            tool_id = f"mcp.{server_id}.{name}"
            async def call(args, c=client, n=name, sid=server_id):
                decision = self.policy.evaluate(sid, n)
                if decision.decision.value == 'BLOCK':
                    return {'ok': False, 'output': f'MCP policy: {decision.reason}', 'decision': decision.decision.value}
                # ASK is deliberately surfaced to System 1 instead of silently executing.
                if decision.decision.value == 'ASK':
                    return {'ok': False, 'output': f'MCP policy: {decision.reason}', 'decision': decision.decision.value}
                result = await c.call_tool(n, args if isinstance(args, dict) else {})
                if isinstance(result, dict) and 'content' in result:
                    result['content'] = result['content'][:self.policy.max_output_chars]
                return {'ok': True, 'output': str(result)[:self.policy.max_output_chars]}
            self.handlers[tool_id] = call
            self.registry.bind(tool_id, async_handler=call)
        server.metadata['transport'] = 'stdio'
        server.metadata['client'] = client
        return tools

    async def call(self, tool_id: str, arguments: dict[str, Any] | None = None):
        spec = self.registry.get(tool_id)
        if spec is None or not tool_id.startswith("mcp."):
            return {"ok": False, "output": "unknown MCP tool"}
        server_id = tool_id.split(".", 2)[1]
        name = tool_id.split(".", 2)[2]
        decision = self.policy.evaluate(server_id, name)
        if decision.decision.value != "ALLOW":
            return {"ok": False, "output": decision.reason, "decision": decision.decision.value}
        return await self.registry.run_async(tool_id, arguments or {})

    async def disconnect(self, server_id: str):
        server = self.servers[server_id]
        client = server.metadata.pop("client", None)
        if client:
            await client.close()
        prefix = f"mcp.{server_id}."
        for tool_id in list(self.handlers):
            if tool_id.startswith(prefix):
                self.handlers.pop(tool_id, None)
                self.registry.unbind(tool_id)
                spec = self.registry.get(tool_id)
                if spec is not None:
                    spec.enabled = False
        return server
