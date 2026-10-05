# Changelog

All notable changes to Nexora Dot X are documented here.
The format follows Keep a Changelog (https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- CHANGELOG.md started with full project history (V1 through V2.12).

## [2.12] - 2026-10-05

### Added
- Model management actions in the /models UI:
  - per-backend Load (model name/path) and Unload buttons
  - Discover button listing loadable models
    (Ollama pulled models, models/gguf/*.gguf, LiteRT scan)
  - ModelService load/unload/discover with event-bus publishes
  - API routes /api/models/load, /api/models/unload,
    /api/models/discover
- Tests for ModelService (fake router, no runtimes needed).

## [2.11] - 2026-10-04

### Added
- Always-allow grants manager in the /approvals UI:
  persisted grants table with per-rule Revoke button,
  POST /api/grants/revoke (audited).

### Fixed
- Files corrupted by fetch-induced line wraps
  (policy.py, models.py, litert-serve tests) rewritten cleanly.

## [2.10] - 2026-10-04

### Added
- Always-allow grants persisted to SQLite (always_allow table):
  survive restarts, whitespace-normalized, revocable.
- nexora.control.always_allow module (save/load/revoke/list)
  and grants reload at startup.

### Fixed
- litert-serve tests patch settings.local_only directly
  (env var is cached at import time).

## [2.9] - 2026-10-04

### Added
- litert-serve model-bus provider: uses the official
  litert-lm serve OpenAI-compatible server
  (GET /v1/models, POST /v1/chat/completions).
- Loopback URLs allowed in local-only mode (on-device);
  non-loopback URLs blocked while NEXORA_LOCAL_ONLY=true.

## [2.8] - 2026-10-04

### Added
- Official litert-lm CLI integration
  (https://developers.google.com/edge/litert-lm/cli):
  - nexora litert import (HuggingFace imports, local-only gated)
  - nexora litert serve (OpenAI-compatible server, port 9379)
  - nexora litert run CLI options: --cli, --backend cpu|gpu,
    --mtp, --attachment, --vision-backend, --audio-backend
  - nexora/models/litert/cli_bridge.py with litert-lm -> uvx
    fallback resolution.

## [2.7] - 2026-10-04

### Added
- Built-in LiteRT-LM CLI commands: nexora litert install
  (default model litert-community/gemma-4-E2B-it-litert-lm),
  litert run, litert doctor.
- Local-only download guard (PermissionError without
  --allow-network or NEXORA_LOCAL_ONLY=false).
- docs/LITERT.md.

### Fixed
- Broken f-string in ensure_default_model
  (SyntaxError from a split string literal).

## [2.6] - 2026-10-04

### Added
- Approvals "always allow" grants shared process-wide
  via the module-level policy set.
- Memory search kind/confidence badges in the UI.
- ApprovalCenter.decide, MemoryService.search_detailed.

### Fixed
- Dangerous patterns always win over always-allow grants
  (no grant can whitelist rm -rf /).

## [2.5] - 2026-10-04

### Added
- Skill approval lifecycle (submit/approve/reject)
  and /skills UI page.
- Discord + Slack worker channel polling.

## [2.4] - 2026-10-04

### Added
- Chat page with /ws/chat streaming, settings page,
  worker-integrated nexora start.
- ChatService, device profiles, background worker.

## [2.3] - 2026-10-03

### Added
- Memory/models UI pages, chat JS streaming client.
- Auth: login page + Bearer-token API middleware.
- CI workflow (ruff + pytest), failure issues auto-open,
  green runs auto-close them.

## [2.2] - 2026-10-03

### Added
- Memory federation service, model service, auth manager,
  backup/restore system, backup CLI, password hashing.
- Chat page, terminal sessions UI, skills page, docs
  (AUTH, BACKUP).

## [2.1] - 2026-10-03

### Added
- First-run wizard UI, WebSocket endpoint + hub/event bus,
  integrations panel.
- Multi-agent delegation, self-growing skills pipeline,
  Home Assistant integration, notifications.

## [2.0] - 2026-10-02

### Added
- WebSocket hub and event-bus fan-out.

## [1.3] - 2026-10-02

### Added
- GGUF/Ollama providers, browser automation, Git/GitHub/HTTP
  tools, MCP registry, Telegram/Discord/Slack/Email channels,
  persistent scheduler, simulate + chat CLI.

## [1.0] - 2026-10-01

### Added
- Initial release: FastHTML control center UI, CLI, API,
  model bus with built-in LiteRT-LM, bots, tools, skills,
  policy engine (System 1), tests and docs.
