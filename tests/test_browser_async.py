import pytest
from nexora.browser.manager import BrowserManager, BrowserPolicy
from nexora.browser.tools import register_browser_tools
from nexora.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_browser_navigate_is_async_native(monkeypatch):
    class Page:
        async def goto(self, url, wait_until=None): self.url = url
        async def title(self): return "Example"
    manager = BrowserManager(BrowserPolicy(["example.com"]))
    class Session: page = Page()
    manager._sessions["s1"] = Session()
    registry = ToolRegistry()
    register_browser_tools(registry, manager)
    result = await registry.run_async("browser.navigate", {"session_id":"s1", "url":"https://example.com"})
    assert result["ok"]
    assert result["output"] == "Example"
