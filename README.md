# Nexora Dot X

Self-hosted, local-first autonomous AI agent operating system.
Python + FastHTML + SQLite, with LiteRT-LM as the built-in local model runtime.

## What it is

Nexora Dot X is a personal AI control center: specialist "Dots" (autonomous
agents) plan tasks, propose tool actions, and execute work - while a
trust-and-policy layer (System 1) decides what is actually allowed.

## Architecture

- **System 1 (control plane)** - policy engine, approvals, audit log, secrets
- **System 2 (intelligence plane)** - Dots, planner, model bus
- **Model bus** - LiteRT-LM (built-in), optional GGUF/Ollama/remote adapters
- **Memory** - persistent multi-layer SQLite memory
- **Tools** - terminal, filesystem, browser (optional), all policy-gated
- **UI** - FastHTML + HTMX dark control center

## Install

Linux / macOS / Termux:

    python3 -m venv .venv && source .venv/bin/activate
    pip install -e .

Windows:

    py -m venv .venv && .venv\Scripts\activate
    pip install -e .

Optional extras: pip install -e ".[litert,dev]"

## Run

    nexora start          # FastHTML control center at http://127.0.0.1:8000
    nexora doctor         # environment diagnostics
    nexora litert scan    # find .litertlm models
    nexora litert doctor  # LiteRT-LM diagnostics

## Security model

Every agent-proposed action passes the policy engine:

    ALLOW  -> execute
    ASK    -> queued as a user approval
    BLOCK  -> refused and audited

All sensitive operations are written to the append-oriented audit log.

## Local-only mode

With NEXORA_LOCAL_ONLY=true (default) no remote inference, telemetry, or
cloud dependency exists. SQLite, memory, tools and scheduler run offline.

## Tests

    pip install -e ".[dev]" && pytest

## Status

V1 core: FastHTML UI, SQLite persistence, Dot system, task engine,
planner, executor, policy engine, approvals, audit, memory, model bus with
LiteRT-LM, terminal + filesystem tools, CLI. See docs/ for details.
