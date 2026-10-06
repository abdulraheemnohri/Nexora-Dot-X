"""Unified, schema-aware tool registry.

System 1 owns tool authorization; this registry owns tool identity, contracts,
platform metadata, and safe dispatch. Handlers may still apply tool-specific
policy (for example terminal policy) as a defense-in-depth layer.
"""
from dataclasses import dataclass, field
from typing import Any, Callable
import inspect


@dataclass
class ToolSpec:
    id: str
    name: str
    description: str
    risk: str = "medium"          # safe/medium/high/critical
    enabled: bool = True
    timeout: int = 60
    platforms: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {"action": {"type": "string"}},
            "required": ["action"],
            "additionalProperties": False,
        }
    )
    permissions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
        self._handlers: dict[str, Callable] = {}
        self._async_handlers: dict[str, Callable] = {}

    def register(self, spec: ToolSpec, handler=None, async_handler=None):
        self._tools[spec.id] = spec
        self._handlers[spec.id] = handler
        if async_handler is not None:
            self._async_handlers[spec.id] = async_handler

    def bind(self, tool_id: str, handler=None, async_handler=None):
        if tool_id not in self._tools:
            raise KeyError(tool_id)
        if handler is not None:
            self._handlers[tool_id] = handler
        if async_handler is not None:
            self._async_handlers[tool_id] = async_handler

    def unbind(self, tool_id: str):
        self._handlers.pop(tool_id, None)
        self._async_handlers.pop(tool_id, None)

    def get(self, tool_id: str) -> ToolSpec | None:
        return self._tools.get(tool_id)

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def schemas(self) -> list[dict[str, Any]]:
        """Return model/MCP-friendly tool definitions."""
        return [
            {
                "name": spec.id,
                "description": spec.description,
                "input_schema": spec.input_schema,
            }
            for spec in self._tools.values()
            if spec.enabled
        ]

    @staticmethod
    def _validate(value: Any, schema: dict[str, Any], path: str = "$") -> str | None:
        kind = schema.get("type")
        if kind == "object":
            if not isinstance(value, dict):
                return f"{path} must be an object"
            required = schema.get("required", [])
            for key in required:
                if key not in value:
                    return f"{path}.{key} is required"
            if schema.get("additionalProperties") is False:
                unknown = set(value) - set(schema.get("properties", {}))
                if unknown:
                    return f"{path} has unknown fields: {', '.join(sorted(unknown))}"
            for key, child in schema.get("properties", {}).items():
                if key in value:
                    error = ToolRegistry._validate(value[key], child, f"{path}.{key}")
                    if error:
                        return error
            return None
        if kind == "string" and not isinstance(value, str):
            return f"{path} must be a string"
        if kind == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            return f"{path} must be an integer"
        if kind == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            return f"{path} must be a number"
        if kind == "boolean" and not isinstance(value, bool):
            return f"{path} must be a boolean"
        if kind == "array" and not isinstance(value, list):
            return f"{path} must be an array"
        if "enum" in schema and value not in schema["enum"]:
            return f"{path} must be one of {schema['enum']}"
        return None

    def validate(self, tool_id: str, arguments: Any) -> str | None:
        spec = self._tools.get(tool_id)
        if spec is None:
            return f"unknown tool: {tool_id}"
        return self._validate(arguments, spec.input_schema)

    def run(self, tool_id: str, action: str | dict) -> dict:
        spec = self._tools.get(tool_id)
        if spec is None:
            return {"ok": False, "output": f"unknown tool: {tool_id}"}
        if not spec.enabled:
            return {"ok": False, "output": f"tool disabled: {tool_id}"}

        # Preserve the existing string-based handler API while allowing new
        # structured tools to receive JSON-like arguments.
        arguments = {"action": action} if isinstance(action, str) else action
        error = self.validate(tool_id, arguments)
        if error:
            return {"ok": False, "output": f"invalid tool arguments: {error}"}

        handler = self._handlers.get(tool_id)
        if handler is None:
            return {"ok": True, "output": f"{tool_id}: {action} (no handler bound)"}
        try:
            result = handler(action)
        except Exception as exc:
            return {"ok": False, "output": f"{tool_id} error: {exc}"}
        if isinstance(result, dict):
            return result
        return {"ok": True, "output": str(result)}

    async def run_async(self, tool_id: str, action: str | dict) -> dict:
        """Async-native dispatch; sync handlers remain supported."""
        spec = self._tools.get(tool_id)
        if spec is None:
            return {"ok": False, "output": f"unknown tool: {tool_id}"}
        if not spec.enabled:
            return {"ok": False, "output": f"tool disabled: {tool_id}"}
        arguments = {"action": action} if isinstance(action, str) else action
        error = self.validate(tool_id, arguments)
        if error:
            return {"ok": False, "output": f"invalid tool arguments: {error}"}
        try:
            handler = self._async_handlers.get(tool_id)
            if handler is not None:
                result = handler(action)
                if inspect.isawaitable(result):
                    result = await result
            else:
                result = self._handlers.get(tool_id)(action) if self._handlers.get(tool_id) else {"ok": True, "output": f"{tool_id}: {action} (no handler bound)"}
            return result if isinstance(result, dict) else {"ok": True, "output": str(result)}
        except Exception as exc:
            return {"ok": False, "output": f"{tool_id} error: {exc}"}
