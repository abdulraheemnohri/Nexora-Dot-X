from nexora.tools.runtime import build_registry


def test_runtime_registry_contains_core_tools():
    registry = build_registry()
    assert registry.get("terminal") is not None
    assert registry.get("filesystem") is not None


def test_runtime_registry_executes_read_only_terminal():
    registry = build_registry()
    result = registry.run("terminal", "printf nexora")
    assert result["ok"]
    assert "nexora" in result["output"]
