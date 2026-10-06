"""FunctionGemma-style action layer (System 2 -> System 1 bridge).

Turns model output into ActionProposal objects and evaluates every one of
them through the System 1 policy engine. The model NEVER executes anything
directly: it only proposes, System 1 disposes (ALLOW / ASK / BLOCK).
"""
import json
import re
from dataclasses import dataclass

from nexora.control.policy import PolicyEngine

FENCE = chr(96) * 3


@dataclass
class ActionProposal:
    tool: str
    arguments: str
    confidence: float = 0.5
    source: str = "model"

    def key(self) -> str:
        return self.tool + ":" + " ".join(str(self.arguments).split())


_ACTION_RE = re.compile(r"^\s*(?:TOOL|ACTION)\s*[:>]\s*(.+)$", re.M)
_TOOL_TAG_RE = re.compile(r'<tool="([^"]+)"\s*>(.*?)</tool>', re.S)
_JSON_BLOCK_RE = re.compile(
    re.escape(FENCE) + r"(?:json)?\s*(\{.*?\})\s*" + re.escape(FENCE), re.S)


def parse(model_output: str) -> list[ActionProposal]:
    """Extract proposals from fenced JSON blocks, <tool=..> tags or TOOL:/ACTION: lines."""
    proposals: list[ActionProposal] = []
    text = (model_output or "").strip()

    for m in _JSON_BLOCK_RE.finditer(text):
        try:
            obj = json.loads(m.group(1))
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("tool"):
            try:
                conf = float(obj.get("confidence", 0.5))
            except (TypeError, ValueError):
                conf = 0.5
            proposals.append(ActionProposal(
                str(obj["tool"]), str(obj.get("arguments", "")),
                conf, str(obj.get("source", "model"))))

    for tool, args in _TOOL_TAG_RE.findall(text):
        proposals.append(ActionProposal(tool, args.strip()))

    for line in _ACTION_RE.findall(text):
        proposals.append(ActionProposal("terminal", line.strip()))

    seen, out = set(), []
    for p in proposals:
        if p.key() not in seen:
            seen.add(p.key())
            out.append(p)
    return out


def evaluate(proposals: list[ActionProposal], policy: PolicyEngine | None = None) -> list[dict]:
    """Run every proposal through the System 1 policy engine."""
    policy = policy or PolicyEngine()
    results = []
    for p in proposals:
        r = policy.evaluate(p.tool, str(p.arguments))
        results.append({
            "tool": p.tool,
            "arguments": p.arguments,
            "confidence": p.confidence,
            "decision": r.decision.value,
            "risk": r.risk.value,
            "reason": r.reason,
        })
    return results


def propose(model_output: str, policy: PolicyEngine | None = None) -> list[dict]:
    """Convenience pipeline: parse model output -> policy decisions."""
    return evaluate(parse(model_output), policy)
