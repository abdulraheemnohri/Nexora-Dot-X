# Architecture

    FastHTML UI (HTMX)
        |
    Gateway (channels: web, future adapters)
        |
    System 1 Control Plane  <-- the ONLY authority
    policy / approvals / audit / limits / secrets
        |
    Orchestrator + Task Engine
        |
    Dots (agents)  <--  Memory (SQLite, multi-layer)
        |
    Model Router (Model Bus)
        |
    LiteRT-LM | GGUF | Ollama | Transformers | remote (optional)
        |
    Tool Registry (terminal, filesystem, browser, http, git)
        |
    Policy Engine -> ALLOW / ASK / BLOCK -> Execution -> Audit

System 2 (models, agents) can only *propose* actions.
System 1 decides whether they run. Nothing in the intelligence plane can
modify the control plane.
