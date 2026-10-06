"""Process-wide System 1 tool registry bootstrap.

Only explicitly registered local tools are exposed to the Executor. Optional
tools are isolated behind imports so a missing extra never breaks startup.
"""
from nexora.tools.registry import ToolRegistry
from nexora.browser.tools import register_browser_tools


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()

    from nexora.tools import terminal
    terminal.register(registry)

    from nexora.tools import filesystem
    filesystem.register(registry)
    register_browser_tools(registry)

    return registry
