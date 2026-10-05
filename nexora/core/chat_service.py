"""Dot-aware chat service with persistent memory and model routing."""
import json

from nexora.database.models import Dot
from nexora.database.runtime import SessionFactory
from nexora.models.router import ModelRouter
from nexora.memory.manager import MemoryManager


class ChatService:
    def __init__(self, models: ModelRouter | None = None,
                 memory: MemoryManager | None = None):
        self.models = models or ModelRouter()
        self.memory = memory or MemoryManager()

    def _dot(self, dot_id: str | None):
        if not dot_id:
            return None
        with SessionFactory() as session:
            return session.get(Dot, dot_id)

    def _context(self, dot_id: str | None, message: str) -> tuple[str, str]:
        dot = self._dot(dot_id)
        if dot is None:
            return "", message
        memories = self.memory.search(message, bot_id=dot.id, limit=8)
        memory_text = "\n".join(
            f"- {m.content}" for m in memories
        )
        system = "\n".join(
            part for part in (
                "You are Nexora Dot X, an autonomous local-first AI worker.",
                f"Name: {dot.name}",
                f"Mission: {dot.mission}" if dot.mission else "",
                f"Personality: {dot.personality}" if dot.personality else "",
                dot.system_prompt or "",
                "System 1 controls tools, permissions, approvals, and side effects. "
                "Never claim to have executed an action unless a tool result confirms it.",
                f"Relevant memory:\n{memory_text}" if memory_text else "",
            ) if part
        )
        return system, message

    async def _send(self, websocket, kind: str, payload: dict):
        await websocket.send_text(
            json.dumps({"kind": kind, "payload": payload}, ensure_ascii=False)
        )

    async def stream_chat(self, websocket, dot_id: str, message: str,
                          policy: str = "local-only"):
        system, prompt = self._context(dot_id, message)
        provider = self.models.ready(policy)
        if provider is None:
            await self._send(websocket, "chat.error", {
                "error": "No model ready. Install a local model "
                         "(nexora litert scan / models/gguf / ollama pull) "
                         "or configure an allowed provider."
            })
            return

        await self._send(websocket, "chat.start", {
            "dot_id": dot_id,
            "backend": provider.backend,
        })
        text = ""
        try:
            for chunk in provider.stream(prompt, system_prompt=system):
                text += str(chunk)
                await self._send(websocket, "chat.chunk", {"text": str(chunk)})
        except Exception as exc:
            await self._send(websocket, "chat.error", {"error": str(exc)})
            return

        try:
            self.memory.save(
                f"User: {message}\nAssistant: {text}",
                bot_id=dot_id,
                kind="episodic",
            )
        except Exception:
            pass
        await self._send(websocket, "chat.done", {"text": text})

    def reply(self, dot_id: str, message: str, policy: str = "local-only") -> str:
        system, prompt = self._context(dot_id, message)
        provider = self.models.ready(policy)
        if provider is None:
            return (
                "No model ready. Install a local model "
                "(nexora litert scan / models/gguf / ollama pull) "
                "or configure an allowed provider."
            )
        return provider.generate(prompt, system_prompt=system)
