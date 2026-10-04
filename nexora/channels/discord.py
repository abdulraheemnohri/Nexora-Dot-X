"""Discord channel adapter (opt-in)."""
import os
from nexora.channels.gateway import Channel
from nexora.core.task_engine import TaskEngine


class DiscordChannel(Channel):
    name = "discord"

    def enabled(self) -> bool:
        return bool(os.getenv("NEXORA_SECRET_DISCORD_TOKEN"))

    def receive(self, message: dict) -> dict:
        goal = (message.get("text") or "").strip()
        if not goal:
            return {"ok": False, "error": "empty message"}
        t = TaskEngine().create(goal, dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}
