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
    nexora start --with-litert-serve      # + litert-lm OpenAI server (9379)
    nexora doctor                     # environment + provider dia
gnostics
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

Back
ground worker polls (only when tokens are configured):

- Telegram: NEXORA_SEC
RET_TELEGRAM_TOKEN
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


## 0.2.0 Highlights

- **Skills system (end-to-end)**: self-grown/imported skills land in a
  pending queue and REQUIRE explicit user approval (System 1). The AI can
  never activate its own skills. Every skill gets a static safety scan
  (forbidden imports/calls, network access, syntax errors) shown in the
  /skills UI. Approved skills can be run from the UI or CLI - the static
  scan is re-checked before every execution. Per-skill detail view shows
  metadata, scan findings and file listings.
  - CLI: `nexora skills list | approve | reject | scan | run <name>`
- **Model management**: per-backend Load/Unload/Discover in the /models
  UI with live 5-second refresh (HTMX). LiteRT model scanning, Ollama
  and GGUF discovery.
- **litert-lm integration**: official litert-lm CLI bridge
  (`nexora litert list | install | import | run | serve | doctor`),
  OpenAI-compatible local server (`nexora litert serve`, port 9379) and
  `nexora start --with-litert-serve` to auto-attach it.
- **Always-allow grants**: persisted to SQLite, survivable across
  restarts, revocable from the /approvals UI (audited).
- **Richer status**: `nexora status` and `GET /api/status` report
  version, uptime, profile, per-backend model status, approval/grant and
  skill counts. Home page shows a live status dashboard (5s polling).
- **Local-first security**: local-only mode by default; network access
  gated behind explicit approval; dangerous patterns can never be
  whitelisted by grants.
