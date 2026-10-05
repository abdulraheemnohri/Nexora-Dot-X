"""Cross-platform policy-gated terminal tool.

This is a bounded process runner, not a claim of OS-level sandboxing. The
System 1 policy is always evaluated before execution; cwd is resolved once,
the environment is sanitized, and runtime is bounded.
"""
import os
import platform
import subprocess
from pathlib import Path

from nexora.control.audit import audit
from nexora.control.policy import Decision, PolicyEngine
from nexora.tools.registry import ToolSpec


class TerminalTool:
    id = "terminal"

    def __init__(self, cwd: str = ".", timeout: int = 60):
        self.policy = PolicyEngine()
        self.cwd = Path(cwd).expanduser().resolve()
        self.cwd.mkdir(parents=True, exist_ok=True)
        self.timeout = max(1, min(int(timeout), 600))

    def detect_shell(self) -> str:
        system = platform.system()
        if system == "Windows":
            return "powershell"
        return "bash"

    def _environment(self) -> dict[str, str]:
        env = dict(os.environ)
        # Never expose common secret variables as a convenience to model-driven
        # shell commands. Explicit integrations should use the secrets layer.
        for key in list(env):
            upper = key.upper()
            if any(token in upper for token in ("TOKEN", "PASSWORD", "SECRET", "PRIVATE_KEY")):
                env.pop(key, None)
        env["NEXORA_MANAGED_TERMINAL"] = "1"
        return env

    def run(self, command: str, *, dry_run: bool = False) -> dict:
        command = (command or "").strip()
        if not command:
            return {"ok": False, "output": "empty command"}

        decision = self.policy.evaluate(self.id, command, dry_run=dry_run)
        audit(
            "agent", tool=self.id, action=command,
            decision=decision.decision.value, outcome=decision.reason,
        )
        if decision.decision is Decision.BLOCK:
            return {"ok": False, "output": f"BLOCKED: {decision.reason}"}
        if decision.decision is Decision.ASK:
            return {
                "ok": False,
                "output": f"APPROVAL_REQUIRED: {decision.reason}",
                "approval_needed": True,
            }
        if dry_run:
            return {"ok": True, "output": f"[dry-run] {command}"}

        shell = self.detect_shell()
        if shell == "powershell":
            args = ["powershell", "-NoProfile", "-NonInteractive", "-Command", command]
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        else:
            args = ["/bin/bash", "-c", command]
            creationflags = 0

        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.cwd),
                env=self._environment(),
                creationflags=creationflags,
            )
            output = (proc.stdout + proc.stderr)[:8000] or "(no output)"
            return {"ok": proc.returncode == 0, "output": output}
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "output": f"execution timeout after {self.timeout}s",
            }
        except Exception as exc:
            return {"ok": False, "output": f"execution error: {exc}"}


def register(registry) -> ToolSpec:
    spec = ToolSpec(
        "terminal", "Terminal",
        "Run bounded shell commands (System 1 policy-gated).",
        risk="high",
    )
    registry.register(spec, TerminalTool().run)
    return spec
