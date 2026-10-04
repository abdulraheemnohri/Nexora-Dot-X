"""Model Context Protocol integration.

MCP server tools are imported into the same Tool Registry, so every MCP
tool call passes the System 1 policy engine exactly like built-in tools.
"""
import json
from dataclasses import dataclass


@dataclass
class MCPServer:
    name: str
    transport: str  # stdio / http
    command: str = ""
    url: str = ""
    enabled: bool = True


class MCPRegistry:
    def __init__(self):
        self._servers: dict[str, MCPServer] = {}

    def add(self, server: MCPServer):
        self._servers[server.name] = server

    def remove(self, name: str) -> bool:
        return self._servers.pop(name, None) is not None

    def list(self) -> list:
        return list(self._servers.values())

    def get(self, name: str) -> MCPServer | None:
        return self._servers.get(name)

    def tools_for(self, name: str) -> list:
        """List tools exposed by an MCP server via JSON-RPC initialize."""
        s = self.get(name)
        if s is None or not s.enabled:
            return []
        try:
            import subprocess, json
            if s.transport == "stdio" and s.command:
                req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
                proc = subprocess.run(s.command.split(), input=json.dumps(req),
                                     capture_output=True, text=True, timeout=30)
                for line in proc.stdout.splitlines():
                    try:
                        data = json.loads(line)
                        if "result" in data and "tools" in data.get("result", {}):
                            return data["result"]["tools"]
                    except Exception:
                        continue
        except Exception:
            pass
        return []
