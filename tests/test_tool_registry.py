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
