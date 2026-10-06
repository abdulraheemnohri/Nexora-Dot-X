from nexora.tools.registry import ToolRegistry, ToolSpec


def test_registry_exposes_tool_schema_and_validates_arguments():
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            "demo",
            "Demo",
            "Demo tool",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        ),
        lambda args: {"ok": True, "output": args["path"]},
    )

    assert registry.schemas()[0]["name"] == "demo"
    assert registry.validate("demo", {"path": "/tmp"}) is None
    assert registry.validate("demo", {}) == "$.path is required"
    assert registry.validate("demo", {"path": "/tmp", "extra": 1})


def test_registry_preserves_legacy_string_handlers():
    registry = ToolRegistry()
    registry.register(ToolSpec("demo", "Demo", "Demo"), lambda action: action)
    result = registry.run("demo", "hello")
    assert result == {"ok": True, "output": "hello"}


import pytest

@pytest.mark.asyncio
async def test_registry_runs_async_handler_inside_event_loop():
    registry = ToolRegistry()
    registry.register(
        ToolSpec("async-demo", "Async Demo", "Async Demo",
                 input_schema={"type":"object","properties":{"value":{"type":"string"}},"required":["value"],"additionalProperties":False}),
        async_handler=lambda args: {"ok": True, "output": args["value"]},
    )
    assert await registry.run_async("async-demo", {"value":"ok"}) == {"ok":True,"output":"ok"}

@pytest.mark.asyncio
async def test_registry_async_path_keeps_sync_handler_compatible():
    registry = ToolRegistry()
    registry.register(ToolSpec("sync-demo", "Sync Demo", "Sync Demo"), lambda action: action)
    result = await registry.run_async("sync-demo", "hello")
    assert result == {"ok": True, "output": "hello"}
