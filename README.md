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
    nexora chat "hi"                  # one-shot generation via model bus
    nexora status                     # full subsystem health overview
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
| /memory     | federated memory search + add memories (paginated)  |
| /models     | live model backend health, LiteRT scan              |
| /skills     | approve / reject / scan / run skills, .zip import,  |
|             | JSON export                                         |
| /dots       | create Dots, pause/resume, live task views           |
| /tasks      | queue tasks, filter by status, paginated detail view |
| /approvals  | System 1 approval queue for tool actions            |
| /settings   | device profiles, system status                      |

The home page shows a live status dashboard (5s polling) with model health,
approval/grant/skill counts and quick Pause/Resume buttons for every Dot.

## Security model

Every agent-proposed action passes the policy engine:

    ALLOW  -> execute
    ASK    -> queued as a user approval
    BLOCK  -> refused and audited

All sensitive operations are written to the append-oriented audit log.
Self-gr
own skills land in a pending queue and require explicit user approval
from /skills; the AI cannot activate them. Imported skill .zip archives
are safely unpacked, statically scanned, and also land in the pending queue.

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

Incoming messages become tasks for the agent runtime.

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
- **Always-allow grants*
*: persisted to SQLite, survivable across
  restarts, revocable from the /approvals UI (audited).
- **Richer status**: `nexora status` and `GET /api/status` report
  version, uptime, profile, per-backend model status, approval/grant and
  skill counts. Home page shows a live status dashboard (5s polling).
- **Local-first security**: local-only mode by default; network access
  gated behind explicit approval; dangerous patterns can never be
  whitelisted by grants.

## 0.2.38-0.2.50 Highlights

- **CLI**: task/dot management subcommands (`nexora tasks`,
  `nexora dots`, `nexora approvals`), federated memory CLI
  (`nexora memory search | remember | forget`) and a full subsystem
  overview in `nexora status` (models, approvals, grants, skills, tasks,
  dots, memories).
- **Tasks UI**: live 5s polling, 20-per-page pagination, status filter
  (RUNNING/COMPLETED/FAILED/CANCELLED) that survives live refresh, inline
  Cancel and a numbered plan-step breakdown ("Step k/n" + task status)
  in the detail view.
- **Dots UI**: per-Dot detail page with live task polling and a working
  Pause/Resume toggle (also inline on the home dashboard).
- **Memory UI**: debounced live search as you type, paginated results
  (20 per page).
- **Skills UI**: .zip upload import with safe unpack + static scan gate,
  JSON export endpoint (`/api/skills/export`) and a machine-readable
  `/api/skills` listing with per-skill scan results.
- **Home dashboard**: live status card plus pending-approvals badge in
  the nav (e.g. "Approvals (3)").


## TUI

Interactive terminal dashboard:

    nexora tui

Keys: `d` Dots, `t` Tasks, `m` Models, `a` Approvals, `w` watch mode
(auto-refresh), `r` refresh, `:help`, `:status`, `q` quit.

## Channels

| Channel | Activation |
|---------|------------|
| Web      | always on |
| Telegram | NEXORA_SECRET_TELEGRAM_TOKEN |
| Discord  | NEXORA_SECRET_DISCORD_TOKEN |
| Slack    | NEXORA_SECRET_SLACK_TOKEN |
| WhatsApp | NEXORA_SECRET_WHATSAPP_TOKEN |
| Email    | SMTP settings |
| Webhook  | NEXORA_SECRET_WEBHOOK (HMAC-SHA256 + replay window) |
| Signal   | NEXORA_SECRET_SIGNAL + NEXORA_SIGNAL_ENDPOINT |
| Teams    | NEXORA_SECRET_TEAMS + NEXORA_TEAMS_ENDPOINT |
