from pathlib import Path
import pytest
from types import SimpleNamespace

from nexora.database.engine import init_db
from nexora.core.chat_service import ChatService


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send_text(self, t):
        self.sent.append(t)


class FakeProvider:
    def stream(self, message):
        return iter(["hel", "lo"])


@pytest.mark.asyncio
async def test_stream_chat_chunks(tmp_path: Path, monkeypatch):
    init_db(tmp_path / "test.db")
    svc = ChatService()
    monkeypatch.setattr(svc.models, "ready", lambda: FakeProvider())
    ws = FakeWS()
    await svc.stream_chat(ws, "dot1", "hi")
    kinds = [__import__("json").loads(s)["kind"] for s in ws.sent]
    assert kinds == ["chat.start", "chat.chunk", "chat.chunk", "chat.done"]
