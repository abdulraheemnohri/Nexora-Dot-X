"""Structured browser tools exposed to System 2 through ToolRegistry."""
from nexora.browser.manager import BrowserManager, BrowserPolicy
from nexora.tools.registry import ToolRegistry, ToolSpec



async def _create(manager, args):
    session = await manager.create(args["session_id"], headless=args.get("headless", True))
    return {"ok": True, "output": session.session_id}


def register_browser_tools(registry: ToolRegistry, manager: BrowserManager | None = None):
    manager = manager or BrowserManager(policy=BrowserPolicy([]))
    registry.register(ToolSpec(
        id="browser.create_session", name="Create browser session",
        description="Create an isolated browser session.", risk="medium",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"},"headless":{"type":"boolean"}},"required":["session_id"],"additionalProperties":False},
    ), async_handler=lambda a: _create(manager, a))
    registry.register(ToolSpec(
        id="browser.navigate", name="Navigate browser",
        description="Navigate an allowlisted browser session to a URL.", risk="high",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"},"url":{"type":"string"}},"required":["session_id","url"],"additionalProperties":False},
    ), async_handler=lambda a: manager.navigate(a["session_id"], a["url"]))
    registry.register(ToolSpec(
        id="browser.screenshot", name="Browser screenshot",
        description="Capture a screenshot of a running browser session.", risk="medium",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"},"path":{"type":"string"}},"required":["session_id","path"],"additionalProperties":False},
    ), async_handler=lambda a: manager.screenshot(a["session_id"], a["path"]))
    registry.register(ToolSpec(
        id="browser.read_page", name="Read browser page",
        description="Read the current HTML document of a browser session.", risk="medium",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"}},"required":["session_id"],"additionalProperties":False},
    ), async_handler=lambda a: manager.content(a["session_id"]))
    registry.register(ToolSpec(
        id="browser.close_session", name="Close browser session",
        description="Close a browser session.", risk="safe",
        input_schema={"type":"object","properties":{"session_id":{"type":"string"}},"required":["session_id"],"additionalProperties":False},
    ), async_handler=lambda a: manager.close(a["session_id"]))
    return manager
