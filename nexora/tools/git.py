"""Git tool. Destructive ops (push/reset) are policy-gated to ASK."""
import subprocess
from nexora.control.policy import PolicyEngine, Decision
from nexora.control.audit import audit
from nexora.tools.registry import ToolSpec


class GitTool:
    id = "git"

    def __init__(self, cwd: str = "."):
        self.policy = PolicyEngine()
        self.cwd = cwd

    def run(self, command: str) -> dict:
        decision = self.policy.evaluate(self.id, command)
        audit("agent", tool=self.id, action=command,
              decision=decision.decision.value, outcome=decision.reason)
        if decision.decision is Decision.BLOCK:
            return {"ok": False, "output": f"BLOCKED: {decision.reason}"}
        if decision.decision is Decision.ASK:
            return {"ok": False, "output": "APPROVAL_REQUIRED", "approval_needed": True}
        try:
            proc = subprocess.run(["git", *command.split()],
                                  capture_output=True, text=True,
                                  timeout=60, cwd=self.cwd)
            return {"ok": proc.returncode == 0,
                    "output": (proc.stdout + proc.stderr)[:8000] or "(no output)"}
        except Exception as e:
            return {"ok": False, "output": f"git error: {e}"}


def register(registry) -> ToolSpec:
    spec = ToolSpec("git", "Git", "Git operations (status/log/diff safe; push gated).", risk="medium")
    registry.register(spec, GitTool().run)
    return spec
