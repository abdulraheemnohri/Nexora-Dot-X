"""Smoke tests for the TUI dashboard (snapshot/render never raise)."""
from nexora.tui.app import render, snapshot


def test_snapshot_never_raises():
    snap = snapshot()
    for key in ("version", "profile", "dots", "tasks", "approvals", "models"):
        assert key in snap


def test_render_contains_header():
    text = render(snapshot())
    assert "NEXORA DOT X" in text
    assert "SYSTEM 1" in text
    assert "SYSTEM 2" in text
    assert "[q]" in text
