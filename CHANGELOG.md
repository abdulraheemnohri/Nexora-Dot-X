# Changelog

All notable changes to Nexora Dot X are documented here.
The format follows Keep a Changelog (https://keepachangelog.com/en/1.1.0/).

## [2.45] - 2026-10-05

### Changed
- Task detail view: plan steps are now a numbered
  breakdown - each step shows "Step k/n" and the plan
  header shows the total step count plus the task
  status, so execution progress is easier to read.

## [Unreleased]

### Added
- CHANGELOG.md started with full project history (V1 through V2.13).

## [2.44] - 2026-10-05

### Added
- nexora memory CLI group (same federated memory as
  the UI):
  - nexora memory search <query> [--limit]
  - nexora memory remember <content> [--kind]
    [--importance]
  - nexora memory forget <query> [--yes] (asks for
    confirmation by default)

## [2.43] - 2026-10-05

### Added
- Dot detail page: the task list is now live - it polls
  every 5 seconds via GET /api/dots/{dot_id}/tasks/rows,
  so queued tasks appear without a reload. The page no
  longer renders a stale static snapshot.

## [2.42] - 2026-10-05

### Added
- Skills page: "Import a skill (.zip)" upload form
  (POST /api/skills/upload, multipart). The archive is
  unpacked safely (path-traversal guarded), statically
  scanned, and only queued for approval - never
  auto-activated (System 1).

## [2.41] - 2026-10-05

### Added
- Memory page live search: the search box now also runs a
  debounced live search (400 ms) via GET /api/memory/rows -
  results appear as you type, no button press needed. The
  explicit Search button (POST /api/memory/search) still works.

### Changed
- server.py rebuilt from sha-verified git history; task
  pagination (V2.38) behavior is unchanged.

## [2.40] - 2026-10-05

### Added
- nexora approvals CLI group (human-in-the-loop decisions
  from the terminal, matching the Approvals UI):
  - nexora approvals list (pending approvals)
  - nexora approvals approve <id> [--always] (also saves
    a persistent always-allow rule)
  - nexora approvals reject <id>

## [2.39] - 2026-10-05

### Added
- nexora skills validate <zip> [--url]: dry-run check of a skill
  archive - unpacks to a temp dir only (nothing is imported),
  validates skill.json, lists files and runs the full static
  safety scan. Import and validate now share one unpack helper.

## [2.38] - 2026-10-05

### Added
- Tasks live table pagination: 20 tasks per page with page
  links (GET /api/tasks/rows?page=N), working together with the
  status filter. Page links are HTMX - no reload needed.

## [2.37] - 2026-10-05

### Added
- nexora dots CLI group:
  - nexora dots list [--enabled]
  - nexora dots create <name> [--mission]
  - nexora dots detail <id> (profile + recent tasks)
  - nexora dots toggle <id> (enable/pause)
## [2.36] - 2026-10-05

### Added
- Dot detail page now has a "Queue a task" form (hidden dot_id,
  goal input) - new tasks can be queued directly from the Dot.

## [2.35] - 2026-10-05

### Added
- Cancel button on every non-terminal task row in the /tasks live
  table (POST /api/tasks/cancel sets status CANCELLED).
  Completed/Failed/Cancelled tasks show no cancel button.

## [2.34] - 2026-10-05

### Added
- nexora skills import --url <url>: downloads a skill .zip from a
  URL and imports it into the pending queue. Network access is
  opt-in: without --allow-network the command refuses to contact
  the network (local-only default preserved).
## [2.33] - 2026-10-05

### Added
- Tasks page status filter: All / RUNNING / COMPLETED / FAILED /
  CANCELLED links (GET /api/tasks/rows?status=...) narrow the
  live task table without a reload.

## [2.32] - 2026-10-05

### Added
- nexora tasks CLI group:
  - nexora tasks list [--status] [--limit]
  - nexora tasks detail <id> (goal, plan steps, result, error)
  - nexora tasks cancel <id> (sets status to CANCELLED)
- nexora status now also reports the total task count.

## [2.31] - 2026-10-05

### Added
- Dot detail page (GET /dots/{id}): full Dot profile (mission,
  personality, model, enabled, workspace) plus all of its tasks
  with statuses. Every Dot card links to it.
- Queued tasks now record their planner steps (set_plan), so the
  task Detail view shows real plan steps.

### Fixed
- server.py used the deprecated TaskService shim with a stale
  constructor call and swapped create(dot_id, goal) arguments.
  Now uses TaskEngine directly with the correct
  create(goal, dot_id=...) signature.
## [2.30] - 2026-10-05

### Added
- Dots enable/pause toggle: POST /api/dots/toggle flips the

  enabled flag and redirects to /dots. Every Dot card now shows
  its status and a Pause/Resume button (paused Dots are excluded
  from chat and new work).

## [2.29] - 2026-10-05

### Added
- Tasks page live view: HTMX polling every 5s via
  GET /api/tasks/rows - statuses update without a reload.
- Per-task Detail button (POST /api/tasks/detail): shows ID, dot,
  goal, status, priority, result, error, created/updated times
  and the recorded plan steps.

## [2.28] - 2026-10-05

### Added
- nexora skills import <archive.zip>: unpacks the archive to a
  temp dir, locates skill.json, and imports the skill into the
  pending queue (skills/.pendin
g). Imported skills still require
  explicit user approval before they run (System 1).

## [2.23] - [2.27] - 2026-10-05

### Added (backfill of previously undocumented releases)
- Skills scanner findings shown directly in the /skills UI
  (static scan column plus per-skill Scan buttons).
- Approved-skill runtime, live approvals dashboard and
  per-skill Detail view (partially documented under 2.17/2.21/2.22).
- nexora skills CLI: list/approve/reject/scan/run/export.
- GET /api/skills JSON endpoint for integrations.
## [2.22] - 2026-10-05

### Added
- Home page live status dashboard: HTMX polling
  (every 5s) via GET /api/status/card - shows version,
  profile, uptime, local-only/auth flags, ready model,
  per-backend model table, approval/grant/skill counts.

## [2.21] - 2026-10-05

### Added
- Per-skill detail view in the /skills UI:
  - Detail button on every pending and active skill
  - POST /api/skills/detail shows the skill metadata
    table, static scan findings and file listing
    (names + sizes) from the skill directory.

## [0.2.0] - 2026-10-05

### Added
- nexora status CLI is now richer and aligned with
  GET /api/status: version, profile, local-only/auth flags,
  host:port, ready backend, per-backend model list, pending
  approvals, always-allow grants and skill counts.
  (Gracefully falls back if runtime details
 are unavailable.)

### Changed
- Version bumped 0.1.0 -> 0.2.0 (pyproject.toml and
  nexora.__version__), so /api/status and the CLI report 0.2.0.

## [2.18] - 2026-10-05

### Added
- /models page live refresh: HTMX polling (every 5s)
  via GET /api/models/rows; backend status changes
  appear without a manual reload.

## [2.17] - 2026-10-05

### Added
- Approved-skill execution support:
  - nexora/skills/runtime.py: run_skill() imports an
    approved skill's tools/main.py and calls run(payload)
  - security: only active (user-approved) skills run;
    the static safety scan is re-checked before execution
  - Run button with input payload in 
the /skills UI
  - POST /api/skills/scan and POST /api/skills/run routes
  - Static scan column for active skills too
  - tests/test_skill_runtime.py (5 tests)

## [2.16] - 2026-10-05

### Added
- Skill scanner findings surfaced in the /skills UI:
  - Static scan column for ev

ery pending skill (forbidden
    imports/calls, network use, syntax errors)
  - Scan button to re-run the safety scan on demand
  - POST /api/skills/scan route
- scan_skill_files() helper in nexora/skills/scanner.py
  (scans all Python files of a skill directory).
- Tests for the skill scanner (tests/test_skill_scanner.py).

## [2.15] - 2026-10-05

### Added
- Richer /api/status: version, uptime, profile, auth and
  local-only flags, per-backend model list, pending approvals,
  always-allow grants and pending skills count
s.

## [2.14] - 2026-10-05

### Added
- nexora start --with-litert-serve [--serve-port N]:
  auto-attaches the litert-lm OpenAI-compatible server to the
  worker startup.

## [2.13] - 2026-10-05

### Added
- CHANGELOG.md covering the full project history (V1 through V2.12).

## [2.12] - 2026-10-05

### Added
- Model management actions in the /models UI:
  - per-backend Load (model name/path) and Unload buttons
  - Discover button listing loadabl
e models
    (Ollama pulled models, models/gguf/*.gguf, LiteRT scan)
  - ModelService load
/unload/discover with event-bus publishes
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
- Always-allow grants persisted to SQLite (always_allow tabl
e):
  survive restarts, whitespace-normalized, revocable.
- nexora.control.alw
ays_allow module (save/load/revoke/list)
  and grants reload at startup.

### Fixed
- litert-serve tests patch settings.local_only directly
  (env var is cached at import time).

## [2.9] - 2026-10-04

### Added
- litert-serve model-bus provider: uses the official
  litert-lm s
e
rve OpenAI-compatible server
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
    --mtp, --attachment, 
--vision-backend, --audio-backend
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
- Broken f-string in
 ensure_default_model
  (SyntaxError from a split string literal).

## [2.6] - 2026-1
0-04

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
  worker-integrated nexora s
tart.
- ChatService, device profiles, background worker.

## [2.3] - 2026
-10-03

### Added
- Memory/models UI pages, chat JS streaming client.
- Auth: login page + Bearer-token API middleware.
- CI workflow (ruff + pytest), failure issues auto-open,
  green runs auto-close them.

## [2.2] - 2026-10-03

### Added
- Memory federation service, model ser
vi
ce, auth manager,
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