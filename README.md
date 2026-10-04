# Nexora Dot X

Self-hosted, local-first autonomous AI agent operating system.
Python + FastHTML + SQLite, with LiteRT-LM as the built-in local model runtime.

## What it is

Nexora Dot X is a personal AI control center: specialist "Dots" (autonomous
agents) plan tasks, propose tool actions, delegate to each other, and execute
work - while a trust-and-policy layer (System 1) decides what is actually
allowed. The AI can think, plan, learn and propose; it can never self-authorize.

## Architecture

- **System 1 (control plane)** - policy engine (ALLOW/ASK/BLOCK), approvals, audit log, secrets
- **System 2 (intelligence plane)** - Dots, planner, delegation, model bus
- **Model bus** - LiteRT-LM (built-in), GGUF, Ollama, optional remote adapters
- **Memory** - persistent multi-layer SQLite memory
- **Tools** - terminal, filesystem, browser, git, github, http, MCP - all policy-gated
- **Channels** - web, Telegram, Discord, Slack, Email, WhatsApp adapter
- **Integrations** - MCP, Home Assistant
- **UI** - FastHTML + HTMX dark control center + WebSocket live activity + setup wizard

## Install

Linux / macOS / Termux:

    python3 -m venv .venv && source .venv/bin/activate
    pip install -e .

Windows:

    py -m venv .venv && .venv\Scripts\activate
    pip install -e .

Optional extras: pip install -e ".[litert,browser,dev]"

## Run

    nexora start          # FastHTML control center at http://127.0.0.1:8000
    nexora doctor         # environment + provider diagnostics
    nexora chat "hi"      # one-shot generation via model bus
    nexora simulate "research AI news"   # dry-run: plan + policy, no side effects
    nexora litert scan     # find .litertlm models
    nexora litert doctor   # LiteRT-LM diagnostics

First run: open http://127.0.0.1:8000/wizard for the setup wizard.

## Security model

Every agent-proposed action passes the policy engine:

    ALLOW  -> execute
    ASK    -> queued as a user approval
    BLOCK  -> refused and audited

All sensitive operations are written to the append-oriented audit log.
Self-grown skills require user approval; the AI cannot activate them.

## Local-only mode

With NEXORA_LOCAL_ONLY=true (default) no remote inference, telemetry, or
cloud dependency exists. SQLite, memory, tools and scheduler run offline.

## Tests

    pip install -e ".[dev]" && pytest

## Status

- V1 core: UI, DB, Dots, tasks, planner, executor, policy, approvals, audit,
  memory, model bus, terminal + filesystem tools, CLI
- V1.1-V1.3: GGUF/Ollama, browser automation, Git/GitHub/HTTP tools, MCP,
  Telegram/Discord/Slack/Email channels, persistent scheduler
- V2: WebSocket live activity, multi-agent delegation, self-growing skills,
  Home Assistant, notifications, first-run wizard

See docs/ for details.
