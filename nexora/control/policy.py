"""System 1 Policy Engine.

System 2 (models/agents) only ever *proposes* actions; every proposal must be
evaluated here before any tool runs. Nothing in the intelligence plane may
bypass evaluate().
"""
import re
from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
    ALLOW = "allow"
    ASK = "ask"
    BLOCK = "block"


class Risk(Enum):
    SAFE = "safe"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


DANGEROUS_PATTERNS = [
    r"rms+-rf", r"mkfs", r"dds+if=", r":()s*{.*};s*:",
    r"shutdown", r"reboot", r"chmods+777s+/",
    r">s*/dev/sd", r"curl[^|]*|s*(ba)?sh",
    r"historys+-c", r"cat.*(id_rsa|.env|credentials)",
]

ASK_PATTERNS = [
    r"apt", r"pips+install", r"npms+install",
    r"gits+push", r"gits+reset", r"systemctl",
    r"sudo", r"kill", r"mv", r"rm",
]

SAFE_PATTERNS = [
    r"^(ls|pwd|whoami|date|uname|cat|echo|grep|find|head|tail|wc|df|du|free|ps|git status|git log|git diff|git branch)$",
    r"^git (add|commit|status|log|diff|branch)",
]


@dataclass
class PolicyResult:
    decision: Decision
    risk: Risk
    reason: str
    matched_rule: str = ""


class PolicyEngine:
    """Rule-based command/tool gate. Global first, extensible per-tool later."""

    def __init__(self):
        self._dangerous = [re.compile(p) for p in DANGEROUS_PATTERNS]
        self._ask = [re.compile(p) for p in ASK_PATTERNS]
        self._safe = [re.compile(p) for p in SAFE_PATTERNS]
        self.allowed_always: set = set()  # (tool, normalized action) approved "always"

    def evaluate(self, tool: str, action: str, *, dry_run: bool = False) -> PolicyResult:
        action = (action or "").strip()
        key = (tool, " ".join(action.split()))
        if key in self.allowed_always:
            return PolicyResult(Decision.ALLOW, Risk.MEDIUM, "previously approved as always")
        for rx in self._dangerous:
            if rx.search(action):
                return PolicyResult(Decision.BLOCK, Risk.CRITICAL,
                                    f"matched dangerous rule {rx.pattern}", rx.pattern)
        for rx in self._safe:
            if rx.match(action):
                return PolicyResult(Decision.ALLOW, Risk.SAFE, "safe-listed command", rx.pattern)
        for rx in self._ask:
            if rx.search(action):
                return PolicyResult(Decision.ASK, Risk.HIGH,
                                    "requires user approval", rx.pattern)
        if tool in ("filesystem.read", "memory", "calculator"):
            return PolicyResult(Decision.ALLOW, Risk.SAFE, "read-only tool")
        if dry_run:
            return PolicyResult(Decision.ALLOW, Risk.MEDIUM, "dry run: no side effects")
        return PolicyResult(Decision.ASK, Risk.MEDIUM, "unknown action: default requires approval")
