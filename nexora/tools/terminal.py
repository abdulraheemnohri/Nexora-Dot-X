"""Cross-platform terminal tool (Linux/Windows/macOS/Termux/WSL/SSH).

Every command passes through the System 1 PolicyEngine before execution.
"""
import platform
import subprocess
from pathlib import Path
from nexora.control.policy import PolicyEngine, Decision
from nexora.control.audit import audit
from nexora.tools.registry import ToolSpec


class TerminalTool:
    id = "terminal"

    def __init__(self, cwd: str = "."):
        self.policy = PolicyEngine()
        self.cwd = Path(cwd).resolve()

    def detect_shell(self) -> str:
        system = platform.system()
        if system == "Windows":
            return "powershell"
        return "bash"

    def run(self, command: str, *, dry_run: bool = False) -> dict:
        decision = self.policy.evaluate(self.id, command, dry_run=dry_run)
        audit("agent", tool=self.id, action=command,
              decision=decision.decision.value, outcome=decision.reason)
        if decision.decision is Decision.BLOCK:
            return {"ok": False, "output": f"BLOCKED: {decision.reason}"}
        if decision.decision is Decision.ASK:
            return {"ok": False, "output": f"APPROVAL_REQUIRED: {decision.reason}",
                    "approval_needed": True}
        if dry_run:
            return {"ok": True, "output": f"[dry-run] {command}"}
        shell = self.detect_shell()
        if shell == "powershell":
            args = ["powershell", "-NoProfile", "-Command", command]
        else:
            args = ["/bin/bash", "-c", command]
        try:
            proc = subprocess.run(args, capture_output=True, text=True,
                                  timeout=60, cwd=str(self.cwd))
            return {"ok": proc.returncode == 0,
                    "output": (proc.stdout + proc.stderr)[:8000] or "(no output)"}
        except Exception as e:
            return {"ok": False, "output": f"execution error: {e}"}


def register(registry) -> ToolSpec:
    spec = ToolSpec("terminal", "Terminal", "Run shell commands (policy-gated).", risk="high")
    registry.register(spec, TerminalTool().run)
    return spec
