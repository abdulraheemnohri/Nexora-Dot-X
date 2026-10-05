"""MCP runtime adapters with bounded stdio lifecycle.

This layer only transports MCP JSON-RPC-like messages. Authorization remains in
System 1 and tool exposure remains controlled by MCPGateway/ToolRegistry.
"""
import asyncio
import json
from dataclasses import dataclass
from typing import Any

@dataclass
class MCPProcessConfig:
    command: list[str]
    cwd: str | None = None
    timeout: float = 30.0

class MCPStdioClient:
    def __init__(self, config: MCPProcessConfig):
        if not config.command:
            raise ValueError("MCP command cannot be empty")
        self.config = config
        self.process = None
        self._next_id = 0

    async def start(self):
        if self.process and self.process.returncode is None:
            return
        self.process = await asyncio.create_subprocess_exec(
            *self.config.command, cwd=self.config.cwd,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

    async def close(self):
        if not self.process: return
        if self.process.returncode is None:
            self.process.terminate()
            try: await asyncio.wait_for(self.process.wait(), 2)
            except asyncio.TimeoutError:
                self.process.kill(); await self.process.wait()
        self.process = None

    async def request(self, method: str, params: dict[str, Any] | None = None):
        await self.start()
        self._next_id += 1
        request_id = self._next_id
        payload = {"jsonrpc":"2.0","id":request_id,"method":method,
                   "params":params or {}}
        self.process.stdin.write((json.dumps(payload) + "\\n").encode())
        await self.process.stdin.drain()
        while True:
            line = await asyncio.wait_for(self.process.stdout.readline(), self.config.timeout)
            if not line: raise RuntimeError("MCP server closed stdout")
            message = json.loads(line.decode())
            if message.get("id") == request_id:
                if "error" in message: raise RuntimeError(str(message["error"]))
                return message.get("result")

    async def list_tools(self):
        result = await self.request("tools/list")
        return list((result or {}).get("tools", []))

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None):
        return await self.request("tools/call", {"name": name, "arguments": arguments or {}})
