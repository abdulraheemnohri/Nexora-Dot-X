from nexora.tools.registry import ToolSpec


def register(registry) -> ToolSpec:
    from nexora.browser.manager import BrowserManager
    mgr = BrowserManager()
    spec = ToolSpec("browser", "Browser", "Playwright browser automation (policy-gated).",
                    risk="high")
    registry.register(spec, mgr.run)
    return spec
