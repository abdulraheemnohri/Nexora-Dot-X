"""MCP-specific System 1 security gate."""
from dataclasses import dataclass, field
from nexora.control.policy import Decision, Risk, PolicyResult

@dataclass
class MCPPolicy:
    trusted_servers: set[str] = field(default_factory=set)
    allowed_servers: set[str] = field(default_factory=set)
    blocked_tools: set[str] = field(default_factory=set)
    max_output_chars: int = 12000

    def evaluate(self, server_id: str, tool_name: str) -> PolicyResult:
        if server_id not in self.allowed_servers:
            return PolicyResult(Decision.BLOCK, Risk.HIGH, "MCP server is not allowlisted")
        full = f"mcp.{server_id}.{tool_name}"
        if full in self.blocked_tools or tool_name in self.blocked_tools:
            return PolicyResult(Decision.BLOCK, Risk.CRITICAL, "MCP tool is blocked")
        if server_id in self.trusted_servers:
            return PolicyResult(Decision.ALLOW, Risk.MEDIUM, "trusted MCP server")
        return PolicyResult(Decision.ASK, Risk.HIGH, "untrusted MCP tool requires approval")

    def sanitize_environment(self, env: dict[str, str] | None):
        if not env: return {}
        blocked = ("TOKEN", "PASSWORD", "SECRET", "PRIVATE_KEY", "API_KEY")
        return {k: v for k, v in env.items() if not any(x in k.upper() for x in blocked)}
