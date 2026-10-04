# Nexora Dot X

[![tests](https://github.com/abdulraheemnohri/Nexora-Dot-X/actions/workflows/test.yml/badge.svg)](https://github.com/abdulraheemnohri/Nexora-Dot-X/actions/workflows/test.yml)

Self-hosted, local-first autonomous AI agent operating system.
Python + FastHTML + SQLite, with LiteRT-LM as the built-in local model runtime.

## What it is

Nexora Dot X is a personal AI control center: specialist "Dots" (autonomous
agents) plan tasks, propose tool actions, delegate to each other, and execute
work - while a trust-and-policy layer (System 1) decides what is actually
allowed. The AI can think, plan, learn and propose; it can never self-authorize.

## Architecture

- **System 1 (control plane)** - policy engine (ALLOW/ASK/BLOCK), approvals,
  audit log, secrets, skill approval gate
- **System 2 (intelligence plane)** - Dots, planner, delegation, model bus
- **Model bus** - LiteRT-LM (built-in), GGUF, Ollama, optional remote adapters
- **Memory** - persistent multi-layer SQLite memory + federated dedupe search
- **Tools** - terminal, filesystem, browser, git, github, http, MCP - all policy-gated
- **Channels** - web, Telegram, Discord, Slack, Email, WhatsApp adapter
- **Worker** - always-on loop: schedules, channel polling, queued task execution
- **Integrations** - MCP, Home Assistant
- **UI** - FastHTML + HTMX control center + WebSocket streaming + setup wizard
- **Profiles** - battery-saver / balanced / performance device profiles

## Install

Linux / macOS / Termux:

    python3 -m venv .venv && source .venv/bin/activate
    pip install -e .

Windows:

    py -m venv .venv && .venv\Scripts\activate
    pip install -e .

Optional extras: pip install -e ".[litert,browser,dev]"

## Run

    nexora start                      # server + background worker
    nexora start --profile battery-saver   # low-power device profile
    nexora doctor                     # environment + provider diagnostics
    nexora chat "hi"                  # one-shot generation via mode

l bus
    nexora simulate "research AI news" # dry-run: plan + policy, no side effects
    nexora litert install             # download the built-in Gemma model
    nexora litert import -y           # import into the official litert-lm registry
    nexora litert run "hello"         # one-shot generation with LiteRT-LM
    nexora litert run "hi" --cli --backend gpu --mtp   # official CLI options
    nexora litert serve               # OpenAI-compatible server (port 9379)
    nexora litert scan                # find .litertlm models
    nexora litert doctor              # LiteRT-LM diagnostics

First run: open http://127.0.0.1:8000/wizard for the setup wizard.

## Web UI

| Page        | Purpose                                             |
|-------------|-----------------------------------------------------|
| /chat       | streaming chat with any enabled Dot (WebSocket)     |
| /memory     | federated memory search + add memories              |
| /models     | live model backend health, LiteRT scan              |
| /skills     | approve / reject self-grown skills                  |
| /approvals  | System 1 approval queue for tool actions            |
| /settings   | device profiles, system status                      |

## Security model

Every agent-proposed action passes the policy engine:

    ALLOW  -> execute
    ASK    -> queued as a user approval
    BLOCK  -> refused and audited

All sensitive operations are written to the append-oriented audit log.
Self-grown skills land in a pending queue and require explicit user approval
from /skills; the AI cannot activate them.

Optional auth: enable with NEXORA_AUTH_ENABLED=true (see docs/AUTH.md) -
pages get a login, API routes take a Bearer token.

## Local-only mode

With NEXORA_LOCAL_ONLY=true (default) no remote inference, network tool calls,
telemetry or uploads happen. Flip to false to allow remote model fallback.

## Channels

Background worker polls (only when tokens are configured):

- Telegram: NEXORA_SECRET_TELEGRAM_TOKEN
- Discord:  NEXORA_SECRET_DISCORD_TOKEN + NEXORA_DISCORD_CHANNEL_ID
- Slack:    NEXORA_SECRET_SLACK_BOT_TOKEN + NEXORA_SLACK_CHANNEL_ID

Incoming m
essages become tasks for the agent runtime.

## CI

Every push runs ruff + pytest on Python 3.12
(.github/workflows/test.yml). Failures open an issue automatically;
green runs close them.

## License

MIT
