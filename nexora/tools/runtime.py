"""Process-wide System 1 tool registry bootstrap.

Only explicitly registered local tools are exposed to the Executor. Optional
tools are isolated behind imports so a missing extra never breaks startup.
"""
from nexora.tools.registry import ToolRegistry


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()

    from nexora.tools import terminal
    terminal.register(registry)

    from nexora.tools import filesystem
    filesystem.register(registry)

    return registry
