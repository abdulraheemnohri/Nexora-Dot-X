"""Microsoft Teams channel adapter. Opt-in; token from NEXORA_SECRET_TEAMS."""
import os

from nexora.channels.gateway import Channel
from nexora.core.task_engine import TaskEngine


class TeamsChannel(Channel):
    name = "teams"

    def enabled(self) -> bool:
        return bool(os.getenv("NEXORA_SECRET_TEAMS"))

    def receive(self, message: dict) -> dict:
        goal = (message.get("text") or "").strip()
        if not goal:
            return {"ok": False, "error": "empty message"}
        t = TaskEngine().create(goal, dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}

    def send(self, chat_id: str, text: str) -> bool:
        import httpx
        endpoint = os.getenv("NEXORA_TEAMS_ENDPOINT")
        token = os.getenv("NEXORA_SECRET_TEAMS")
        if not endpoint or not token:
            return False
        try:
            r = httpx.post(endpoint, json={"chat_id": chat_id, "text": text},
                           headers={"Authorization": "Bearer " + token}, timeout=30)
            return r.status_code in (200, 201)
        except Exception:
            return False
