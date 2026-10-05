from nexora.browser.tools import register_browser_tools
from nexora.tools.registry import ToolRegistry


def test_browser_tools_publish_schemas():
    registry = ToolRegistry()
    register_browser_tools(registry)
    names = {x["name"] for x in registry.schemas()}
    assert {"browser.create_session", "browser.navigate", "browser.screenshot", "browser.read_page", "browser.close_session"} <= names


def test_browser_navigate_schema_is_strict():
    registry = ToolRegistry()
    register_browser_tools(registry)
    assert registry.validate("browser.navigate", {"session_id": "s", "url": "https://example.com"}) is None
    assert registry.validate("browser.navigate", {"url": "https://example.com"})
    assert registry.validate("browser.navigate", {"session_id": "s", "url": 1})
