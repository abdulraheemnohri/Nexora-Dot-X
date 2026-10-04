"""Telegram channel adapter. Opt-in; token from NEXORA_SECRET_TELEGRAM_TOKEN."""
import os
from nexora.channels.gateway import Channel
from nexora.core.task_engine import TaskEngine


class TelegramChannel(Channel):
    name = "telegram"

    def enabled(self) -> bool:
        return bool(os.getenv("NEXORA_SECRET_TELEGRAM_TOKEN"))

    def receive(self, message: dict) -> dict:
        goal = (message.get("text") or "").strip()
        if not goal:
            return {"ok": False, "error": "empty message"}
        t = TaskEngine().create(goal, dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}

    def send(self, chat_id: str, text: str) -> bool:
        import httpx
        token = os.getenv("NEXORA_SECRET_TELEGRAM_TOKEN")
        if not token:
            return False
        try:
            r = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage",
                           json={"chat_id": chat_id, "text": text}, timeout=30)
            return r.status_code == 200
        except Exception:
            return False
