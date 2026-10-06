"""Shared channel ingress/egress gateway.

All channels normalize inbound events here. The gateway never executes tools
directly; it hands goals to the durable task/worker pipeline.
"""
from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from nexora.core.task_engine import TaskEngine

@dataclass
class ChannelMessage:
    channel: str
    sender: str
    text: str
    dot_id: str | None = None
    reply_target: str | None = None
    metadata: dict[str, Any] | None = None

class Channel:
    name = "base"
    def receive(self, message: dict) -> dict:
        raise NotImplementedError

class WebChannel(Channel):
    name = "web"
    def __init__(self, tasks: TaskEngine | None = None):
        self.tasks = tasks or TaskEngine()
    def receive(self, message: dict) -> dict:
        goal = str(message.get("text", "")).strip()
        if not goal:
            return {"ok": False, "error": "empty message"}
        t = self.tasks.create(goal, dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}

class Gateway:
    def __init__(self, tasks: TaskEngine | None = None,
                 submit: Callable[[str | None, str], Awaitable[Any]] | None = None):
        self.tasks = tasks or TaskEngine()
        self.submit = submit
        self._channels: dict[str, Channel] = {}

    def register(self, channel: Channel):
        self._channels[channel.name] = channel

    def route(self, channel_name: str, message: dict) -> dict:
        ch = self._channels.get(channel_name)
        if ch is None:
            return {"ok": False, "error": f"channel not enabled: {channel_name}"}
        return ch.receive(message)

    async def route_async(self, channel_name: str, message: dict) -> dict:
        text = str(message.get("text", "")).strip()
        if not text:
            return {"ok": False, "error": "empty message"}
        if self.submit is None:
            return self.route(channel_name, message)
        task = await self.submit(message.get("dot_id"), text)
        return {"ok": True, "task_id": getattr(task, "id", str(task))}

    def channels(self):
        return sorted(self._channels)
