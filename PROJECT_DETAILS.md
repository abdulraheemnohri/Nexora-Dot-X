# Nexora Dot X — Complete Project Details

> Self-hosted, local-first autonomous AI agent operating system.
> Python + FastHTML + SQLite, LiteRT-LM as the built-in local model runtime.

---

## 1. What Nexora Dot X Is

Nexora Dot X is a personal AI control center. Specialist **Dots**
(autonomous agents) plan tasks, propose tool actions, delegate to each
other and execute work — while a trust-and-policy layer decides what is
actually allowed.

**The core rule:** the AI can think, plan, learn and propose. It can
never self-authorize.

### Two-Plane Architecture

| Plane | Name | Role |
|---|---|---|
| Control plane | **System 1** | Policy engine (ALLOW / ASK / BLOCK), approvals, audit log, secrets, skill approval gate |
| Intelligence plane | **System 2** | Dots, planner, delegation, model bus |

Every action proposed by System 2 must pass through `PolicyEngine.evaluate()`
in System 1 before any tool runs. Nothing in the intelligence plane can
bypass it.

---

## 2. Features (Complete List)

### 2.1 Dots (Autonomous Agents)
- Create specialist agents with a name, description, mission,
  personality, system prompt and model.
- Each Dot has a lifecycle status: online / working / waiting / paused /
  error / offline.
- Pause / resume (enable / disable) any Dot from the home page
  (quick-toggle) or the Dots page.
- Dot's tasks are listed live with HTMX polling (5s).

### 2.2 Tasks (Autonomous Work)
- Queue a task for a Dot by goal text; the heuristic **Planner**
  decomposes the goal into steps (analyze / tool / review kinds).
- Full task lifecycle:
  `CREATED → QUEUED → PLANNING → RUNNING → WAITING_APPROVAL → PAUSED →
  RETRYING → COMPLETED | FAILED | CANCELLED`.
- Numbered, multi-step plans are created and stored as JSON per task.
- Filter tasks by **status** (RUNNING / COMPLETED / FAILED / CANCELLED)
  and by **Dot** (V2.52) — plus a dot filter dropdown on the UI (V2.53).
- Paginated task table (20 per page) with live polling, per-task
  Detail and Cancel buttons.
- Task filter state persists while polling (V2.49).

### 2.3 Approvals (Human-in-the-Loop)
- Any tool action the policy engine rates as risky becomes a pending
  approval with a reason and risk level.
- User can: **Approve once**, **Always allow this** (persisted grant),
  or **Reject**.
- Always-allow grants are stored in SQLite and survive restarts; the
  in-memory hot set is synchronized on startup.
- The approvals badge in the home nav shows the pending count (V2.46).

### 2.4 Skills (Self-Grown / Imported Capabilities)
- Skills land in `skills/.pending/` and MUST be approved by the user
  before activation — the AI cannot activate its own skills.
- Static security scan of every skill file before approval and again
  before every execution.
- Upload skills as `.zip`, or import from a local path / URL
  (network opt-in).
- Run approved skills with a text payload from the UI or CLI.
- **Export any skill as JSON** (V2.47).
- **Detail view** shows metadata, scan findings, the file list, and
  inline previews of the first three text files (≤4KB each, V2.54).

### 2.5 Memory (Multi-Layer, Persistent)
- Kinds: working / episodic / semantic / procedural / user / project.
- Each record has source, tags, project id, importance, confidence and
  privacy level.
- Search with pagination (V2.50), remember new facts, forget (delete)
  with confirmation.
- Federated dedupe search across instances.
- Memory counts in the CLI status output (V2.48).

### 2.6 Models (Model Bus)
- Backends: LiteRT-LM (built-in local), GGUF, Ollama, optional remote
  adapters.
- Model Router reports honest per-backend health: ready / not installed.
  **Nexora never fakes a model** — if nothing is ready you get an honest
  install hint.
- Discover / load / unload models from the Models page.
- LiteRT-LM CLI bridge: install models from Hugging Face repos, run
  prompts (with speculative/MTP, vision and audio backend options), and
  optionally start the official litert-lm OpenAI-compatible server
  (127.0.0.1:9379) alongside Nexora.

### 2.7 Chat (Streaming)
- Per-Dot WebSocket chat with **token-level streaming**
  (`chat.start`, `chat.chunk`, `chat.error` events).
- Dot selector reconnects the socket; chat history is memory-aware.

### 2.8 Audit Log (System 1 Transparency)
- Append-only audit entry for **every sensitive operation**: actor
  (system / agent / orchestrator / user), tool, action, decision,
  outcome and timestamp.
- Written by: policy evaluation, approvals, always-allow grants, skill
  execution, worker pause/resume.
- **Audit viewer page** `/audit` shows the last 100 entries with a nav
  link on the home page (V2.54).

### 2.9 Worker Controls
- Always-on background worker drives: due schedules (SQLite-backed,
  survive restarts), channel polling (Telegram / Discord / Slack — each
  only when its token is set), and queued task execution.
- **Pause / resume task processing** from the Settings page
  (V2.54): while paused, new tasks stay QUEUED; the toggle itself is
  audited.

### 2.10 Security & Auth
- Optional password login (`NEXORA_AUTH_ENABLED`) with an
  httponly cookie session via `AuthMiddleware`.
- Local-only by default (binds 127.0.0.1).
- Dangerous-command blocklist (rm -rf, mkfs, fork bombs, curl|sh,
  reading private keys …), ask-list for installs/git push/sudo, and a
  safe-command allowlist.

### 2.11 Live Dashboard
- Home status card (5s polling): version, profile, uptime, local-only,
  auth, ready model, pending approvals, always-allow grants, pending
  skills, **live task counts (running/queued/completed/failed, V2.54)**.
- Quick Pause/Resume toggle per Dot right on the home page (V2.50).

---

## 3. Web UI (Pages & Endpoints)

### Pages
| Route | Purpose |
|---|---|
| `/` | Home: nav, live status card, dot quick-toggles |
| `/dots` | Dots: create, list, detail, pause/resume |
| `/chat` | Streaming chat with Dot selector |
| `/memory` | Memory: search (paginated), remember, forget |
| `/models` | Model bus: status table, discover/load/unload |
| `/skills` | Skills: upload zip, pending + active tables, approve/reject/scan/run/detail |
| `/tasks` | Tasks: queue form, status + dot filters, live paginated table |
| `/approvals` | Pending approval cards: approve / always-allow / reject |
| `/audit` | Audit log viewer (last 100 entries) |
| `/settings` | Profiles table, system info, worker pause/resume, logout |
| `/login` | Password login (when auth is enabled) |

### API Endpoints
| Endpoint | Method | Function |
|---|---|---|
| `/api/status` | GET | Runtime status JSON (mirrors CLI status) |
| `/api/status/card` | GET | Live home dashboard HTML fragment |
| `/api/dots`, `/api/dots/toggle` | POST | Create dot / pause-resume dot |
| `/api/dots/`… (rows/detail) | GET/POST | Live dot lists & details |
| `/api/tasks` | POST | Queue a task for a Dot |
| `/api/tasks/rows` | GET | Live task table fragment (status, dot, page params) |
| `/api/tasks/detail`, `/api/tasks/cancel` | POST | Task detail / cancel |
| `/api/approvals/<id>/approve\|always\|reject` | POST | Decide a pending approval |
| `/api/skills/upload` | POST | Import a skill zip (multipart) |
| `/api/skills/approve\|reject\|scan\|detail\|run` | POST | Skill lifecycle actions |
| `/api/skills/export` | GET | Export a skill as JSON |
| `/api/memory/rows\|remember\|forget` | GET/POST | Memory UI fragments & mutations |
| `/api/models/load\|unload\|discover` | POST/GET | Model bus actions |
| `/api/worker/toggle` | POST | Pause/resume task processing |
| `/ws/chat?dot_id=` | WS | Streaming chat WebSocket |
| `/auth/login`, `/auth/logout` | POST | Login / logout |

All HTML fragments escape user-supplied content (`<` → `&lt;`) to
prevent XSS.

---

## 4. CLI (nexora command, Typer-based)

| Command | Function |
|---|---|
| `nexora status` | Version, profile, host/port, ready model, per-backend health, pending approvals, grants, skills, task count, dots (total/enabled), memories |
| `nexora start [--profile] [--with-litert-serve] [--serve-port]` | Start FastHTML server + background worker |
| `nexora doctor` | Environment diagnosis |
| `nexora litert list` | List installed LiteRT models |
| `nexora litert install -r <repo> [-y]` | Download a model (network opt-in) |
| `nexora litert import` | Import a downloaded .litertlm file |
| `nexora litert run <prompt> [-m model] [-b backend] [--mtp] [-a attachment] [--cli]` | Run a prompt locally |
| `nexora litert serve` | Start the official litert-lm OpenAI-compatible server |
| `nexora litert doctor` | LiteRT environment diagnosis |
| `nexora skills list [--pending-only]` | List skills |
| `nexora skills approve\|reject <name>` | Skill decisions |
| `nexora skills scan <name>` | Static security scan |
| `nexora skills run <name> [-p payload]` | Run an approved skill |
| `nexora skills validate [archive] [-u url]` | Validate a zip before import |
| `nexora skills import` | Import + submit a skill for approval |
| `nexora skills export <name> [-o out]` | Export skill as JSON |
| `nexora tasks list [--status] [--dot] [--limit]` | List tasks |
| `nexora tasks detail\|cancel <id>` | Task detail / cancel |
| `nexora dots list [--enabled-only]`, `create`, `detail`, `toggle` | Dot management |
| `nexora approvals list\|approve <id> [-a]\|reject <id>` | Approvals from terminal |
| `nexora memory search\|remember\|forget` | Memory from terminal |

---

## 5. Settings (Environment Variables)

| Variable | Default | Meaning |
|---|---|---|
| `NEXORA_HOST` | `127.0.0.1` | Server bind host (local-only by default) |
| `NEXORA_PORT` | `8000` | Server port |
| `NEXORA_DATA_DIR` | `./data` | Data dir; SQLite DB at `data/nexora.db` |
| `NEXORA_MODEL_DIR` | `./models` | Model storage root |
| `NEXORA_LITERT_DIR` | `./models/litert` | LiteRT model dir |
| `NEXORA_WORKSPACE_DIR` | `./workspaces` | Dot workspaces |
| `NEXORA_SKILLS_DIR` | `./skills` | Skills root (`skills/.pending` for unapproved) |
| `NEXORA_LOCAL_ONLY` | `true` | Local-only mode |
| `NEXORA_AUTH_ENABLED` | `false` | Require password login |
| `NEXORA_LOG_LEVEL` | `INFO` | Logging level |
| `NEXORA_DEFAULT_MODEL` | `litert` | Default model backend |
| `NEXORA_PROFILE` | `balanced` | Device profile (below) |

### Device Profiles
| Profile | Workers | Poll | Browser | Context |
|---|---|---|---|---|
| `battery-saver` | 1 | 60s | no | 1024 |
| `balanced` | 3 | 15s | yes | 4096 |
| `performance` | 8 | 5s | yes | 8192 |

Profiles bound worker count, polling frequency, browser usage and model
context size so Nexora can run on phones (Termux), laptops and servers.
Select via env var or `nexora start --profile <name>`. Unknown names fall
back to `balanced`.

Channel tokens (Telegram / Discord / Slack) enable each channel's polling
in the background worker — each polls only when its token is set.

---

## 6. Database (SQLite, SQLAlchemy)

| Table | Purpose |
|---|---|
| `dots` | Agents: name, description, mission, personality, system prompt, model, template, status, enabled, workspace, timestamps |
| `tasks` | Goal, dot_id FK, plan (JSON), status, priority, result, error, timestamps |
| `approvals` | Tool, action, reason, risk, status (pending/approved/rejected), decided_at |
| `always_allow` | Persisted always-allow grants |
| `memories` | bot_id, kind, content, source, tags, project_id, importance, confidence, privacy, created_at |
| `audit_logs` | actor, bot_id, task_id, tool, action, decision, outcome, created_at |
| `events` | Event bus history (kind, payload, created_at) |

Repository pattern (`nexora.database.repositories`): `add_obj`,
`get_all`, `get_by_id`, `update_fields`, `delete_by_id`, `query`.

---

## 7. Key Modules & Functions

| Module | Key functions / classes |
|---|---|
| `core/task_engine.py` | `TaskEngine.create/list/get/set_status/set_plan/get_plan` |
| `core/planner.py` | `Planner.plan(goal) → steps` (heuristic; model-driven when a provider is configured) |
| `core/model_service.py` | `status/ready_backend/scan_litert/discover/load/unload` |
| `core/chat_service.py` | `ChatService.stream_chat(websocket, dot_id, message)` |
| `core/memory_service.py` | remember / search / forget with pagination |
| `core/profiles.py` | `PROFILES`, `get_profile(name)` |
| `core/executor.py` | `Executor.execute/resume` — policy-gated step execution |
| `core/orchestrator.py` | `Orchestrator.authorize(tool, action)` — System 1 entry |
| `control/policy.py` | `PolicyEngine.evaluate`, `Decision` (ALLOW/ASK/BLOCK), `Risk`, pattern lists |
| `control/approvals.py` | `ApprovalCenter.request/pending/approve/reject/decide` |
| `control/always_allow.py` | `save_grant/list_grants/load_grants/revoke` |
| `control/audit.py` | `audit(actor, …)`, `tail(limit)`, `render(entry)` |
| `skills/manager.py` | `SkillManager.scan/pending/inspect/submit/…` |
| `skills/runtime.py` | `run_skill(skill, payload)` — active-only, re-scans before run |
| `skills/scanner.py` | `scan_skill_files(skill)` — static security scan |
| `automation/worker.py` | `BackgroundWorker.start/stop` — scheduler, channels, queued tasks |
| `security/auth.py` + `middleware.py` | `AuthManager.login`, `AuthMiddleware`, cookie session |
| `server.py` | `create_app()` — all routes above, live HTMX fragments |

---

## 8. Task Worker Behavior (V2.54+)

- Default state: **running**.
- `POST /api/worker/toggle` flips `paused` and writes an audit entry
  (actor `user`, decision PAUSE/RESUME).
- While paused, `runtime_submit` still creates the task but leaves it in
  `QUEUED` with the result note "Task processing is paused" — no planning
  runs. Already-running tasks are untouched.
- Settings page shows live state (`running` / `PAUSED`) and the profile's
  max workers.

---

## 9. Version History (Recent)

- **2.45** — Numbered plan steps in task detail
- **2.46** — Approvals pending-count badge in nav
- **2.47** — Skills JSON export
- **2.48** — CLI status: dot + memory counts
- **2.49** — Task filter persists across polling
- **2.50** — Home dot quick-toggle, memory pagination, dots form fix
- **2.51** — README feature documentation
- **2.52** — Filter tasks by dot (URL param + engine filter)
- **2.53** — Dot filter dropdown on the Tasks page
- **2.54** — Audit viewer, skill file previews, worker pause controls, live task counts

(Full history in `CHANGELOG.md`.)

---

## 10. Security Summary

- Every tool action passes the System 1 policy gate; nothing self-authorizes.
- Dangerous patterns hard-blocked; risky categories require user approval.
- Skills are quarantined until user-approved and re-scanned before every run.
- All web output is HTML-escaped; auth cookie is httponly + samesite=lax.
- Local-only by default; network features (downloads, imports) are opt-in.
- Every sensitive decision is recorded in the append-only audit log.
