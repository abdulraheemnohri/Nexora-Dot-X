"""Signal channel adapter. Opt-in; token from NEXORA_SECRET_SIGNAL."""
import os

from nexora.channels.gateway import Channel
from nexora.core.task_engine import TaskEngine


class SignalChannel(Channel):
    name = "signal"

    def enabled(self) -> bool:
        return bool(os.getenv("NEXORA_SECRET_SIGNAL"))

    def receive(self, message: dict) -> dict:
        goal = (message.get("text") or "").strip()
        if not goal:
            return {"ok": False, "error": "empty message"}
        t = TaskEngine().create(goal, dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}

    def send(self, chat_id: str, text: str) -> bool:
        import httpx
        endpoint = os.getenv("NEXORA_SIGNAL_ENDPOINT")
        token = os.getenv("NEXORA_SECRET_SIGNAL")
        if not endpoint or not token:
            return False
        try:
            r = httpx.post(endpoint, json={"recipient": chat_id, "message": text},
                           headers={"Authorization": "Bearer " + token}, timeout=30)
            return r.status_code == 200
        except Exception:
            return False
