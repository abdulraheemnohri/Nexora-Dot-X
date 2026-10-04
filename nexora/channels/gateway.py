"""Channel gateway: maps inbound messages to identity, Dot and task.

Concrete adapters (Telegram, Discord, Slack, WhatsApp, Email, Teams) plug
into the same pipeline; every routed action still passes System 1.
"""
from nexora.core.task_engine import TaskEngine


class Channel:
    name = "base"

    def receive(self, message: dict) -> dict:
        raise NotImplementedError


class WebChannel(Channel):
    name = "web"

    def __init__(self):
        self.tasks = TaskEngine()

    def receive(self, message: dict) -> dict:
        goal = message.get("text", "").strip()
        if not goal:
            return {"ok": False, "error": "empty message"}
        t = self.tasks.create(goal, dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}


class Gateway:
    def __init__(self):
        self._channels: dict[str, Channel] = {}

    def register(self, channel: Channel):
        self._channels[channel.name] = channel

    def route(self, channel_name: str, message: dict) -> dict:
        ch = self._channels.get(channel_name)
        if ch is None:
            return {"ok": False, "error": f"channel not enabled: {channel_name}"}
        return ch.receive(message)
