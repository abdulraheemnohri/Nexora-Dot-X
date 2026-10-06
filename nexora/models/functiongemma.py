"""FunctionGemma-compatible action proposal adapter."""
import json
from typing import Any, Callable, Awaitable
from nexora.core.action_bridge import ActionBridge, ActionProposal

class FunctionGemmaAdapter:
    """Runtime-agnostic action adapter; inference is injected."""
    def __init__(self, bridge: ActionBridge,
                 infer: Callable[[str], str | Awaitable[str]] | None = None):
        self.bridge = bridge
        self.infer = infer

    @staticmethod
    def parse_output(text: str) -> ActionProposal:
        raw = text.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1]) if len(lines) >= 3 else raw
        payload = json.loads(raw)
        return ActionProposal(
            tool=str(payload["tool"]),
            arguments=dict(payload.get("arguments") or {}),
            confidence=float(payload.get("confidence", 0.0)),
            source=str(payload.get("source", "functiongemma")),
        )

    async def propose(self, prompt: str):
        if self.infer is None:
            raise RuntimeError("FunctionGemma inference backend is not configured")
        result = self.infer(prompt)
        if hasattr(result, "__await__"):
            result = await result
        return self.parse_output(str(result))

    async def execute(self, prompt: str):
        proposal = await self.propose(prompt)
        dispatch = getattr(self.bridge, "dispatch_async", None)
        if dispatch is None:
            return self.bridge.dispatch(proposal)
        return await dispatch(proposal)
