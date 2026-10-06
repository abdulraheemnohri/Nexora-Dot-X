"""Verified webhook channel: HMAC signature + timestamp replay window."""
import hashlib
import hmac
import os
import time

from nexora.channels.gateway import Channel
from nexora.core.task_engine import TaskEngine

REPLAY_WINDOW_SECONDS = 300


def verify_signature(secret: str, payload: str, signature: str) -> bool:
    """Constant-time HMAC-SHA256 check. Never trust an unsigned webhook."""
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, str(signature).strip().lower())


class WebhookChannel(Channel):
    name = "webhook"

    def enabled(self) -> bool:
        return bool(os.getenv("NEXORA_SECRET_WEBHOOK"))

    def receive(self, message: dict) -> dict:
        secret = os.getenv("NEXORA_SECRET_WEBHOOK", "")
        payload = message.get("text") or ""
        signature = message.get("signature") or ""
        ts = message.get("timestamp") or 0
        if not self.enabled():
            return {"ok": False, "error": "webhook channel disabled"}
        if not verify_signature(secret, payload, signature):
            return {"ok": False, "error": "invalid signature"}
        try:
            if abs(time.time() - float(ts)) > REPLAY_WINDOW_SECONDS:
                return {"ok": False, "error": "stale webhook (replay?)"}
        except (TypeError, ValueError):
            return {"ok": False, "error": "invalid timestamp"}
        if not payload.strip():
            return {"ok": False, "error": "empty message"}
        t = TaskEngine().create(payload, dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}
