"""Tests for the FunctionGemma action layer (propose -> policy)."""
from nexora.control.policy import PolicyEngine
from nexora.models.functiongemma import ActionProposal, evaluate, parse, propose

FENCE = chr(96) * 3


def test_parse_json_block():
    out = parse('thinking... ' + FENCE + 'json {"tool": "terminal", "arguments": "ls -la"} ' + FENCE)
    assert len(out) == 1
    assert out[0].tool == "terminal"
    assert out[0].arguments == "ls -la"


def test_parse_tool_tag_and_action_line():
    out = parse('<tool="filesystem.read">notes.md</tool>' + chr(10) + 'TOOL: git status')
    assert len(out) == 2
    assert out[0].tool == "filesystem.read"
    assert out[1].tool == "terminal"
    assert out[1].arguments == "git status"


def test_parse_dedupe():
    out = parse("TOOL: ls" + chr(10) + "ACTION: ls")
    assert len(out) == 1


def test_policy_blocks_dangerous():
    r = propose("TOOL: rm -rf /")
    assert r[0]["decision"] == "block"


def test_policy_allows_safe():
    r = propose("TOOL: ls")
    assert r[0]["decision"] == "allow"


def test_policy_asks_git_push():
    r = propose("TOOL: git push origin main")
    assert r[0]["decision"] == "ask"


def test_evaluate_empty():
    assert evaluate([], PolicyEngine()) == []


def test_proposal_key_normalized():
    p = ActionProposal("terminal", "git   status")
    assert p.key() == "terminal:git status"
