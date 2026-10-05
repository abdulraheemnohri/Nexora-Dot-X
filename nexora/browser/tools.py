"""Structured browser tools exposed to System 2 through ToolRegistry."""
import asyncio
from nexora.browser.manager import BrowserManager, BrowserPolicy
from nexora.tools.registry import ToolRegistry, ToolSpec


def _run(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError("browser tool must execute outside an active event loop")


def register_browser_tools(registry: ToolRegistry, manager: BrowserManager | None = None):
    manager = manager or BrowserManager(policy=BrowserPolicy([]))
    registry.register(ToolSpec(
        id="browser.create_session", name="Create browser session",
        description="Create an isolated browser session.", risk="medium",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"},"headless":{"type":"boolean"}},"required":["session_id"],"additionalProperties":False},
    ), lambda a: manager.create(a["session_id"], headless=a.get("headless", True)).__dict__)
    registry.register(ToolSpec(
        id="browser.navigate", name="Navigate browser",
        description="Navigate an allowlisted browser session to a URL.", risk="high",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"},"url":{"type":"string"}},"required":["session_id","url"],"additionalProperties":False},
    ), lambda a: _run(manager.navigate(a["session_id"], a["url"])))
    registry.register(ToolSpec(
        id="browser.screenshot", name="Browser screenshot",
        description="Capture a screenshot of a running browser session.", risk="medium",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"},"path":{"type":"string"}},"required":["session_id","path"],"additionalProperties":False},
    ), lambda a: _run(manager.screenshot(a["session_id"], a["path"])))
    registry.register(ToolSpec(
        id="browser.read_page", name="Read browser page",
        description="Read the current HTML document of a browser session.", risk="medium",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"}},"required":["session_id"],"additionalProperties":False},
    ), lambda a: _run(manager.content(a["session_id"])))
    registry.register(ToolSpec(
        id="browser.close_session", name="Close browser session",
        description="Close a browser session.", risk="safe",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"}},"required":["session_id"],"additionalProperties":False},
    ), lambda a: _run(manager.close(a["session_id"])))
    return manager
