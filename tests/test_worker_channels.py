import asyncio

from nexora.automation.worker import BackgroundWorker


class FakeResp:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_discord_poll_creates_task(monkeypatch):
    w = BackgroundWorker()
    seen = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        seen["url"] = url
        seen["params"] = params
        return FakeResp([{"id": "99", "content": "do the thing",
                           "author": {"username": "raheem", "bot": False}},
                          {"id": "100", "content": "bot msg",
                           "author": {"username": "mybot", "bot": True}}])

    monkeypatch.setenv("NEXORA_SECRET_DISCORD_TOKEN", "tok")
    monkeypatch.setenv("NEXORA_DISCORD_CHANNEL_ID", "chan1")
    monkeypatch.setattr("httpx.get", fake_get)

    created = []
    monkeypatch.setattr(w.tasks, "create",
                        lambda goal: created.append(goal) or seen.setdefault("t", goal))
    asyncio.run(w._poll_discord())
    assert seen["url"].endswith("/channels/chan1/messages")
    assert created == ["do the thing"]      # bot's own message ignored
    assert w._dc_after == "99"


def test_slack_poll_skips_bots(monkeypatch):
    w = BackgroundWorker()

    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResp({"ok": True, "messages": [
            {"text": "hello agent", "user": "U1"},
            {"text": "deploy done", "bot_id": "B1"}],
            "response_metadata": {"next_cursor": "cur1"}})

    monkeypatch.setenv("NEXORA_SECRET_SLACK_BOT_TOKEN", "tok")
    monkeypatch.setenv("NEXORA_SLACK_CHANNEL_ID", "C1")
    monkeypatch.setattr("httpx.get", fake_get)

    created = []
    monkeypatch.setattr(w.tasks, "create",
                        lambda goal: created.append(goal) or goal)
    asyncio.run(w._poll_slack())
    assert created == ["hello agent"]
    assert w._sl_cursor == "cur1"


def test_disabled_channels_noop(monkeypatch):
    w = BackgroundWorker()
    monkeypatch.delenv("NEXORA_SECRET_DISCORD_TOKEN", raising=False)
    monkeypatch.delenv("NEXORA_SECRET_SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("NEXORA_SECRET_TELEGRAM_TOKEN", raising=False)
    # must not touch the network at all
    monkeypatch.setattr("httpx.get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network!")))
    asyncio.run(w._poll_telegram())
    asyncio.run(w._poll_discord())
    asyncio.run(w._poll_slack())
