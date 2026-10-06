"""Shared channel ingress/egress gateway with System-1 boundary controls."""
import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

@dataclass
class ChannelMessage:
    channel: str
    sender: str
    text: str
    dot_id: str | None = None
    reply_target: str | None = None
    metadata: dict[str, Any] | None = None

class Gateway:
    def __init__(self, submit: Callable[[str | None, str], Awaitable[Any]] | None = None,
                 secrets: dict[str, str] | None = None, rate_limit: int = 30,
                 window_seconds: int = 60, replay_seconds: int = 300):
        self.submit = submit
        self.secrets = secrets or {}
        self.rate_limit = max(1, rate_limit)
        self.window_seconds = max(1, window_seconds)
        self.replay_seconds = max(1, replay_seconds)
        self._hits: dict[str, list[float]] = {}
        self._seen: dict[str, float] = {}

    def verify_signature(self, channel: str, body: bytes, signature: str | None,
                         timestamp: str | None = None) -> bool:
        secret = self.secrets.get(channel)
        if not secret:
            return True
        if not signature or not timestamp:
            return False
        try:
            ts = float(timestamp)
        except ValueError:
            return False
        if abs(time.time() - ts) > self.replay_seconds:
            return False
        signed = timestamp.encode() + b"." + body
        digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature.removeprefix("sha256="))

    def _rate_ok(self, key: str) -> bool:
        now = time.time()
        hits = [x for x in self._hits.get(key, []) if now - x < self.window_seconds]
        if len(hits) >= self.rate_limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True

    async def route_async(self, channel_name: str, message: dict,
                          body: bytes | None = None, signature: str | None = None,
                          timestamp: str | None = None) -> dict:
        text = str(message.get("text", "")).strip()
        sender = str(message.get("sender", "unknown"))
        if not text:
            return {"ok": False, "error": "empty message"}
        if not self.verify_signature(channel_name, body or text.encode(), signature, timestamp):
            return {"ok": False, "error": "invalid or expired channel signature"}
        if not self._rate_ok(channel_name + ":" + sender):
            return {"ok": False, "error": "rate limit exceeded"}
        if self.submit is None:
            return {"ok": False, "error": "channel gateway is not connected to worker"}
        task = await self.submit(message.get("dot_id"), text)
        return {"ok": True, "task_id": getattr(task, "id", str(task))}
