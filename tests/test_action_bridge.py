from nexora.core.action_bridge import ActionBridge
from nexora.tools.registry import ToolRegistry, ToolSpec


def test_low_confidence_requires_approval():
    r = ToolRegistry()
    r.register(ToolSpec(id="calculator", name="Calculator", description="calc",
                        input_schema={"type":"object","properties":{"action":{"type":"string"}},"required":["action"],"additionalProperties":False}))
    b = ActionBridge(r, min_confidence=.8)
    p = b.parse({"tool":"calculator","arguments":{"action":"2+2"},"confidence":.4})
    result = b.dispatch(p)
    assert result["decision"] == "ask"


def test_invalid_schema_is_blocked():
    r = ToolRegistry()
    r.register(ToolSpec(id="calculator", name="Calculator", description="calc"))
    b = ActionBridge(r)
    p = b.parse({"tool":"calculator","arguments":{},"confidence":1})
    assert b.dispatch(p)["decision"] == "block"
