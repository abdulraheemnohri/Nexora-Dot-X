# MCP (Model Context Protocol)

MCP servers are registered in the MCPRegistry. Their tools are imported into
the unified Tool Registry, which means:

    MCP Server -> MCP Adapter -> Tool Registry -> System 1 Policy -> Execution

MCP tools get exactly the same ALLOW / ASK / BLOCK treatment as built-in
tools. Nothing from an MCP server can bypass the policy engine.
