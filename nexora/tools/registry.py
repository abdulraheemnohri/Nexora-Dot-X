"""Unified tool registry. Every tool declares risk and permissions."""
from dataclasses import dataclass, field


@dataclass
class ToolSpec:
    id: str
    name: str
    description: str
    risk: str = "medium"          # safe/medium/high/critical
    enabled: bool = True
    timeout: int = 60
    platforms: list = field(default_factory=list)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
        self._handlers = {}

    def register(self, spec: ToolSpec, handler=None):
        self._tools[spec.id] = spec
        self._handlers[spec.id] = handler

    def list(self) -> list:
        return list(self._tools.values())

    def run(self, tool_id: str, action: str) -> dict:
        spec = self._tools.get(tool_id)
        if spec is None:
            return {"ok": False, "output": f"unknown tool: {tool_id}"}
        if not spec.enabled:
            return {"ok": False, "output": f"tool disabled: {tool_id}"}
        handler = self._handlers.get(tool_id)
        if handler is None:
            return {"ok": True, "output": f"{tool_id}: {action} (no handler bound)"}
        try:
            return {"ok": True, "output": str(handler(action))}
        except Exception as e:
            return {"ok": False, "output": f"{tool_id} error: {e}"}
