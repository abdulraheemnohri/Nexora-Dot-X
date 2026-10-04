"""Streaming chat service: Dot conversations with token-level streaming.

Every chat turn goes through the Model Router (System 2). If no model is
ready the user gets an honest install hint — never a fake reply.
"""
import json

from nexora.models.router import ModelRouter
from nexora.memory.manager import MemoryManager


class ChatService:
    """Handles Dot chat: model calls, streaming over WebSocket, memory."""

    def __init__(self, models: ModelRouter | None = None, memory: MemoryManager | None = None):
        self.models = models or ModelRouter()
        self.memory = memory or MemoryManager()

    async def _send(self, websocket, kind: str, payload: dict):
        await websocket.send_text(json.dumps({"kind": kind, "payload": payload}, ensure_ascii=False))

    async def stream_chat(self, websocket, dot_id: str, message: str):
        """Stream a chat reply to a WebSocket client.

        Protocol: chat.start -> chat.chunk* -> chat.done (or chat.error).
        """
        provider = self.models.ready()
        if provider is None:
            await self._send(websocket, "chat.error", {
                "error": "No model ready. Install a local model "
                          "(nexora litert scan / models/gguf / ollama pull) "
                          "or configure a remote provider."
            })
            return

        await self._send(websocket, "chat.start", {"dot_id": dot_id})
        text = ""
        try:
            for chunk in provider.stream(message):
                text += str(chunk)
                await self._send(websocket, "chat.chunk", {"text": str(chunk)})
        except Exception as e:  # model failure mid-stream must not be silent
            await self._send(websocket, "chat.error", {"error": str(e)})
            return

        try:
            self.memory.save(f"User: {message}\nAssistant: {text}",
                             bot_id=dot_id, kind="episodic")
        except Exception:
            pass  # memory failure must not lose the reply
        await self._send(websocket, "chat.done", {"text": text})

    def reply(self, dot_id: str, message: str) -> str:
        """Blocking single-shot reply (used by HTMX /api/chat endpoint)."""
        provider = self.models.ready()
        if provider is None:
            return ("No model ready. Install a local model "
                    "(nexora litert scan / models/gguf / ollama pull) "
                    "or configure a remote provider.")
        return provider.generate(message)
