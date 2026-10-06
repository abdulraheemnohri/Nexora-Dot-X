"""Tests for the webhook / signal / teams channel adapters."""
import hashlib
import hmac
import time

from nexora.channels.signal import SignalChannel
from nexora.channels.teams import TeamsChannel
from nexora.channels.webhook import REPLAY_WINDOW_SECONDS, WebhookChannel, verify_signature


def _sig(secret, payload):
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def test_verify_signature_ok():
    assert verify_signature("s3cret", "hello world", _sig("s3cret", "hello world")) is True


def test_verify_signature_bad():
    assert verify_signature("s3cret", "hello", "deadbeef") is False
    assert verify_signature("", "hello", "x") is False
    assert verify_signature("s", "hello", "") is False


def test_webhook_replay_rejected(monkeypatch):
    monkeypatch.setenv("NEXORA_SECRET_WEBHOOK", "k")
    payload = "do something"
    ch = WebhookChannel()
    stale = {"text": payload, "signature": _sig("k", payload),
             "timestamp": time.time() - REPLAY_WINDOW_SECONDS - 10}
    assert ch.receive(stale)["ok"] is False
    bad = {"text": payload, "signature": "bad", "timestamp": time.time()}
    assert ch.receive(bad)["ok"] is False


def test_webhook_disabled_by_default(monkeypatch):
    monkeypatch.delenv("NEXORA_SECRET_WEBHOOK", raising=False)
    ch = WebhookChannel()
    assert ch.enabled() is False
    assert ch.receive({"text": "x"})["ok"] is False


def test_signal_teams_opt_in(monkeypatch):
    monkeypatch.delenv("NEXORA_SECRET_SIGNAL", raising=False)
    monkeypatch.delenv("NEXORA_SECRET_TEAMS", raising=False)
    assert SignalChannel().enabled() is False
    assert TeamsChannel().enabled() is False
    assert SignalChannel.name == "signal"
    assert TeamsChannel.name == "teams"
    assert SignalChannel().send("id", "txt") is False
    assert TeamsChannel().send("id", "txt") is False
