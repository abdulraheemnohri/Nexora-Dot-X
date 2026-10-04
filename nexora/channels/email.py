"""Email channel adapter (IMAP/SMTP, opt-in). Sending requires approval."""
import os
from nexora.channels.gateway import Channel
from nexora.core.task_engine import TaskEngine


class EmailChannel(Channel):
    name = "email"

    def enabled(self) -> bool:
        return bool(os.getenv("NEXORA_SECRET_SMTP_HOST"))

    def receive(self, message: dict) -> dict:
        goal = (message.get("subject", "") + " " + message.get("body", "")).strip()
        if not goal:
            return {"ok": False, "error": "empty message"}
        t = TaskEngine().create(f"[email] {goal}", dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}

    def send(self, to: str, subject: str, body: str) -> dict:
        """Sending always goes through System 1 (AS-level risk)."""
        from nexora.control.orchestrator import Orchestrator
        orch = Orchestrator()
        decision, approval = orch.authorize("email", f"send to {to}: {subject}")
        if approval is not None:
            return {"ok": False, "pending_approval": approval.id}
        if decision.decision.value != "allow":
            return {"ok": False, "error": decision.reason}
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = os.getenv("NEXORA_SECRET_SMTP_FROM", "")
        msg["To"] = to
        with smtplib.SMTP(os.getenv("NEXORA_SECRET_SMTP_HOST", ""),
                          int(os.getenv("NEXORA_SECRET_SMTP_PORT", "587"))) as s:
            s.starttls()
            s.login(os.getenv("NEXORA_SECRET_SMTP_USER", ""),
                    os.getenv("NEXORA_SECRET_SMTP_PASSWORD", ""))
            s.send_message(msg)
        return {"ok": True}
