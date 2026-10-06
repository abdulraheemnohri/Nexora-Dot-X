import pytest
from nexora.models.functiongemma import FunctionGemmaAdapter
from nexora.core.action_bridge import ActionBridge
from nexora.tools.registry import ToolRegistry, ToolSpec

def test_functiongemma_parses_json_proposal():
    proposal = FunctionGemmaAdapter.parse_output(
        '{"tool":"terminal","arguments":{"action":"printf ok"},"confidence":0.9}'
    )
    assert proposal.tool == "terminal"
    assert proposal.arguments["action"] == "printf ok"
    assert proposal.confidence == 0.9

@pytest.mark.asyncio
async def test_functiongemma_keeps_execution_behind_system1():
    registry = ToolRegistry()
    registry.register(ToolSpec("safe", "Safe", "Safe", input_schema={
        "type":"object","properties":{"action":{"type":"string"}},
        "required":["action"],"additionalProperties":False}), lambda a: {"ok":True,"output":"done"})
    bridge = ActionBridge(registry)
    adapter = FunctionGemmaAdapter(bridge, lambda prompt:
        '{"tool":"safe","arguments":{"action":"read-only"},"confidence":1}')
    result = await adapter.execute("do safe thing")
    assert result["ok"]
