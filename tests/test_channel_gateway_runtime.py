import pytest
from nexora.channels.gateway import Gateway

@pytest.mark.asyncio
async def test_gateway_uses_shared_submitter():
    calls = []
    class T:
        id = "task-1"
    async def submit(dot_id, text):
        calls.append((dot_id, text))
        return T()
    gateway = Gateway(submit=submit)
    result = await gateway.route_async("web", {"dot_id":"dot-1", "text":"hello"})
    assert result == {"ok": True, "task_id": "task-1"}
    assert calls == [("dot-1", "hello")]
