"""FastHTML application: the Nexora control center (HTMX + dark UI)."""
import os

from fasthtml.common import *
from starlette.responses import RedirectResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from nexora.config import settings
from nexora.database.engine import init_db
from nexora.database.models import Approval
from nexora.bots.manager import BotManager
from nexora.bots.templates import TEMPLATES
from nexora.core.task_engine import TaskEngine, TaskStatus
from nexora.core.executor import Executor
from nexora.core.events import bus
from nexora.core.ws import hub
from nexora.memory.manager import MemoryManager
from nexora.models.router import ModelRouter
from nexora.models.litert.diagnostics import scan, doctor as litert_doctor
from nexora.tools.registry import ToolRegistry
from nexora.tools import terminal as terminal_tool
from nexora.tools import filesystem as fs_tool
from nexora.tools import git as git_tool
from nexora.tools import github as github_tool
from nexora.tools import http as http_tool
from nexora.tools import browser as browser_tool
from nexora.tools.terminal_sessions import TerminalSessionManager
from nexora.automation.scheduler import Scheduler
from nexora.channels.gateway import Gateway, WebChannel
from nexora.channels.telegram import TelegramChannel
from nexora.channels.discord import DiscordChannel
from nexora.channels.slack import SlackChannel
from nexora.ui.wizard import wizard_page, create_first_dot

NAV = [("Dashboard", "/"), ("Chat", "/chat"), ("Dots", "/dots"), ("Tasks", "/tasks"),
       ("Approvals", "/approvals"), ("Activity", "/activity"),
       ("Models", "/models"), ("Memory", "/memory"),
       ("Terminal", "/terminal"), ("Skills", "/skills"),
       ("Scheduler", "/scheduler"), ("Setup", "/wizard"), ("Settings", "/settings")]


def shell(title, *body):
    nav = Nav(*[A(label, href=href, cls="navlink") for label, href in NAV], cls="nav")
    return Title("Nexora Dot X - " + title), Main(
        H1("Nexora Dot X", cls="brand"), nav, Div(*body, cls="container"))


def create_app():
    init_db()
    settings.ensure_dirs()
    app, rt = fast_app()

    bots = BotManager()
    tasks = TaskEngine()
    memory = MemoryManager()
    models = ModelRouter()
    registry = ToolRegistry()
    for mod in (terminal_tool, fs_tool, git_tool, github_tool, http_tool, browser_tool):
        try:
            mod.register(registry)
        except Exception:
            pass
    executor = Executor(tool_registry=registry)
    scheduler = Scheduler()
    gateway = Gateway()
    gateway.register(WebChannel())
    term_mgr = TerminalSessionManager()

    def _approvals():
        from nexora.database import repositories as repo
        return repo.get_all(Approval, limit=100, order_desc="created_at")

    def _pending():
        return [a for a in _approvals() if a.status == "pending"]

    # ---- auth gate (only when enabled) ----
    if settings.auth_enabled:
        from starlette.middleware.base import BaseHTTPMiddleware

        class AuthMiddleware(BaseHTTPMiddleware):
            PUBLIC = ("/login", "/static")

            async def dispatch(self, request, call_next):
                path = request.url.path
                if path.startswith(self.PUBLIC):
                    return await call_next(request)
                token = request.cookies.get("nx_session", "")
                from nexora.security.auth import AuthManager
                if not AuthManager().valid_session(token):
                    return RedirectResponse("/login", status_code=303)
                return await call_next(request)

        app.add_middleware(AuthMiddleware)

        @rt("/login")
        def login_page():
            return Title("Nexora - Login"), Main(
                Section(H2("Sign in"),
                        Form(Input(name="password", type="password",
                                   placeholder="Password", required=True),
                             Button("Sign in", cls="btn"),
                             action="/api/login", method="post"), cls="card"))

        @rt("/api/login", methods=["POST"])
        def login(password: str):
            from nexora.security.auth import AuthManager
            token = AuthManager().login(password)
            if token is None:
                return RedirectResponse("/login", status_code=303)
            resp = RedirectResponse("/", status_code=303)
            resp.set_cookie("nx_session", token, httponly=True)
            return resp

    @rt("/")
    def dashboard():
        running = [t for t in tasks.list() if t.status == TaskStatus.RUNNING.value]
        return shell("Dashboard",
            Section(H2("System status"),
                    P("Mode: " + ("LOCAL ONLY" if settings.local_only else "hybrid")),
                    P("Active Dots: " + str(sum(1 for d in bots.list() if d.status != "offline"))),
                    P("Running tasks: " + str(len(running))),
                    P("Pending approvals: " + str(len(_pending()))),
                    P("Model bus: " + (", ".join(
                        m.name + "=" + m.status for m in models.available()) or "none")),
                    cls="card"),
            Section(H2("Recent activity"),
                    *((Li(e.kind) for e in bus.tail(10)) if bus.tail(10)
                      else [P("No activity yet.")]),
                    cls="card"))

    # ---- Chat page: real model-bus generation with streaming fallback ----
    @rt("/chat")
    def chat_page(dot_id: str = ""):
        dots = bots.list()
        return shell("Chat",
            Section(H2("Chat with a Dot"),
                    Form(Select(*[Option(d.name, value=d.id) for d in dots]
                                or [Option("(no dots)", value="")],
                                name="dot_id"),
                         Input(name="message", placeholder="Message", required=True),
                         Button("Send", cls="btn"),
                         action="/api/chat", method="post"), cls="card"),
            Section(H2("Reply"),
                    Div(id="chat-output"), cls="card"))

    @rt("/api/chat", methods=["POST"])
    def chat(dot_id: str = "", message: str = ""):
        from nexora.core.events import bus as _bus
        _bus.publish("chat.message", {"dot_id": dot_id, "message": message})
        try:
            reply = models.generate(message)
        except Exception as e:
            reply = ("Model unavailable: " + str(e) +
                     "\n\n(Install a local model: models/litert/, models/gguf/, "
                     "or run Ollama. See docs/MODELS.md)")
        if dot_id:
            memory.save("User: " + message, bot_id=dot_id, kind="working")
            memory.save("Assistant: " + reply[:500], bot_id=dot_id, kind="working")
        return shell("Chat",
            Section(H2("Chat with a Dot"),
                    Form(Select(name="dot_id"), Input(name="message",
                                                      placeholder="Message",
                                                      required=True),
                         Button("Send", cls="btn"),
                         action="/api/chat", method="post"), cls="card"),
            Section(H2("Reply"), P(reply), cls="card"))

    @rt("/dots")
    def dots_page():
        items = bots.list()
        return shell("Dots",
            Section(H2("Create Dot"),
                    Form(Input(name="name", placeholder="Name", required=True),
                         Input(name="mission", placeholder="Mission"),
                         Input(name="personality", placeholder="Personality"),
                         Button("Create", cls="btn"),
                         action="/api/dots", method="post"), cls="card"),
            Section(H2("From template"),
                    Form(Select(*[Option(v["name"], value=k)
                                  for k, v in TEMPLATES.items()], name="template"),
                         Button("Create from template", cls="btn"),
                         action="/api/dots/template", method="post"), cls="card"),
            Section(H2("Dots"), *[
                Div(H3(d.name + " - " + d.status),
                    P(d.mission or "No mission"),
                    A("start", href="/api/dots/" + d.id + "/start"),
                    " | ", A("pause", href="/api/dots/" + d.id + "/pause"),
                    " | ", A("stop", href="/api/dots/" + d.id + "/stop"),
                    " | ", A("duplicate", href="/api/dots/" + d.id + "/duplicate"),
                    cls="dot-card") for d in items] or [P("No Dots yet.")], cls="card"))

    @rt("/api/dots", methods=["POST"])
    def create_dot(name: str, mission: str = "", personality: str = ""):
        bots.create(name=name, mission=mission, personality=personality)
        return RedirectResponse("/dots", status_code=303)

    @rt("/api/dots/template", methods=["POST"])
    def create_dot_from_template(template: str):
        if template in TEMPLATES:
            bots.create_from_template(template)
        return RedirectResponse("/dots", status_code=303)

    @rt("/api/dots/{dot_id}/start")
    def start_dot(dot_id: str):
        bots.start(dot_id)
        return RedirectResponse("/dots", status_code=303)

    @rt("/api/dots/{dot_id}/pause")
    def pause_dot(dot_id: str):
        bots.pause(dot_id)
        return RedirectResponse("/dots", status_code=303)

    @rt("/api/dots/{dot_id}/stop")
    def stop_dot(dot_id: str):
        bots.stop(dot_id)
        return RedirectResponse("/dots", status_code=303)

    @rt("/api/dots/{dot_id}/duplicate")
    def duplicate_dot(dot_id: str):
        bots.duplicate(dot_id)
        return RedirectResponse("/dots", status_code=303)

    @rt("/tasks")
    def tasks_page():
        return shell("Tasks",
            Section(H2("Queue task"),
                    Form(Input(name="goal", placeholder="Goal", required=True),
                         Input(name="dot_id", placeholder="Dot ID (optional)"),
                         Button("Queue", cls="btn"),
                         action="/api/tasks", method="post"), cls="card"),
            Section(H2("Tasks"), *[
                Div(H3("[" + t.status + "] " + t.goal),
                    P("id " + t.id + " | dot " + str(t.dot_id)),
                    P(t.result or t.error or ""),
                    A("cancel", href="/api/tasks/" + t.id + "/cancel"),
                    cls="task-card") for t in tasks.list(50)] or [P("No tasks.")],
                cls="card"))

    @rt("/api/tasks", methods=["POST"])
    async def create_task(goal: str, dot_id: str = ""):
        t = tasks.create(goal, dot_id=dot_id or None)
        tasks.set_status(t.id, TaskStatus.QUEUED.value)
        dot = bots.get(dot_id) if dot_id else None
        if dot is not None:
            from nexora.core.agent import Agent
            await Agent(dot, executor=executor).run_task(t)
        return RedirectResponse("/tasks", status_code=303)

    @rt("/api/tasks/{task_id}/cancel")
    def cancel_task(task_id: str):
        tasks.set_status(task_id, TaskStatus.CANCELLED.value)
        return RedirectResponse("/tasks", status_code=303)

    @rt("/approvals")
    def approvals_page():
        return shell("Approvals",
            Section(H2("Pending"), *[
                Div(H3(a.tool + ": " + a.action),
                    P("risk " + a.risk + " - " + a.reason),
                    A("Approve once", href="/api/approvals/" + a.id + "/approve"),
                    " | ", A("Approve always",
                             href="/api/approvals/" + a.id + "/approve?always=1"),
                    " | ", A("Reject", href="/api/approvals/" + a.id + "/reject"),
                    cls="approval-card") for a in _pending()]
                or [P("No pending approvals.")], cls="card"))

    @rt("/api/approvals/{aid}/approve")
    def approve(aid: str, always: str = ""):
        from nexora.control.approvals import ApprovalCenter
        ApprovalCenter().approve(aid, always=bool(always))
        return RedirectResponse("/approvals", status_code=303)

    @rt("/api/approvals/{aid}/reject")
    def reject(aid: str):
        from nexora.control.approvals import ApprovalCenter
        ApprovalCenter().reject(aid)
        return RedirectResponse("/approvals", status_code=303)

    @rt("/activity")
    def activity_page():
        events = bus.tail(50)
        return shell("Activity",
            Section(H2("Event timeline"),
                    *((Li(e.kind + ": " + e.payload[:120]) for e in events)
                      if events else [P("No events yet.")]), cls="card"))

    @rt("/models")
    def models_page():
        info = scan()
        checks = litert_doctor()
        return shell("Models",
            Section(H2("Model bus"),
                    *(P(m.name + ": " + m.status + " - " + m.detail)
                      for m in models.available()), cls="card"),
            Section(H2("LiteRT-LM"),
                    *(P(c) for c in checks),
                    H3("Installed models"),
                    *((P(m["name"] + " (" + str(m["size"]) + " bytes, context "
                         + str(m["context"]) + ")") for m in info["models"])
                      if info["models"] else [P("No .litertlm models installed.")]),
                    cls="card"))

    @rt("/memory")
    def memory_page(q: str = ""):
        rows = memory.search(q)
        return shell("Memory",
            Section(H2("Search"),
                    Form(Input(name="q", placeholder="query", value=q),
                         Button("Search", cls="btn"),
                         action="/memory", method="get"), cls="card"),
            Section(H2("Records"), *[
                Div(P("[" + r.kind + "] " + r.content[:160]), cls="mem-card")
                for r in rows[:50]] or [P("Memory is empty.")], cls="card"))

    # ---- Terminal page ----
    @rt("/terminal")
    def terminal_page():
        return shell("Terminal",
            Section(H2("Run command (policy-gated)"),
                    Form(Input(name="command", placeholder="command",
                               required=True),
                         Button("Run", cls="btn"),
                         action="/api/terminal", method="post"),
                    P("SAFE commands run instantly; dangerous ones are blocked; "
                      "others require approval."), cls="card"),
            Section(H2("Sessions"), *[
                Div(P(s.id + " - " + str(len(s.history)) + " commands"),
                    cls="task-card") for s in term_mgr.list()]
                or [P("No terminal sessions yet.")], cls="card"))

    @rt("/api/terminal", methods=["POST"])
    def run_terminal(command: str, session_id: str = "default"):
        s = term_mgr.get(session_id) or term_mgr.create(session_id)
        result = s.run(command)
        return shell("Terminal",
            Section(H2("Run command (policy-gated)"),
                    Form(Input(name="command", placeholder="command",
                               required=True),
                         Button("Run", cls="btn"),
                         action="/api/terminal", method="post"), cls="card"),
            Section(H2("Output"),
                    Pre("$ " + command + "\n" + result["output"]), cls="card"),
            Section(H2("Sessions"), cls="card"))

    # ---- Skills page ----
    @rt("/skills")
    def skills_page():
        from nexora.skills.manager import SkillManager
        skills = SkillManager().scan()
        return shell("Skills",
            Section(H2("Installed skills"), *[
                Div(H3(s.get("name", "?")),
                    P(s.get("description", "")),
                    P("risk: " + str(s.get("risk", "n/a"))),
                    cls="task-card") for s in skills] or [P("No skills installed. "
                    "Drop folders with skill.json into skills/.")], cls="card"))

    @rt("/scheduler")
    def scheduler_page():
        jobs = scheduler.list()
        return shell("Scheduler",
            Section(H2("Add schedule"),
                    Form(Input(name="goal", placeholder="Goal", required=True),
                         Input(name="every", placeholder="Every N seconds",
                               value="86400"),
                         Input(name="dot_id", placeholder="Dot ID (optional)"),
                         Button("Add", cls="btn"),
                         action="/api/schedules", method="post"), cls="card"),
            Section(H2("Schedules"), *[
                Div(H3(j.goal),
                    P("every " + str(int(j.every_seconds)) + "s | enabled "
                      + str(j.enabled)),
                    A("remove", href="/api/schedules/" + j.id + "/remove"),
                    cls="task-card") for j in jobs] or [P("No schedules.")],
                cls="card"))

    @rt("/api/schedules", methods=["POST"])
    def add_schedule(goal: str, every: str = "86400", dot_id: str = ""):
        try:
            scheduler.add(goal, float(every), dot_id=dot_id or None)
        except ValueError:
            pass
        return RedirectResponse("/scheduler", status_code=303)

    @rt("/api/schedules/{job_id}/remove")
    def remove_schedule(job_id: str):
        scheduler.remove(job_id)
        return RedirectResponse("/scheduler", status_code=303)

    @rt("/api/scheduler/run-due")
    def run_due():
        scheduler.run_due()
        return RedirectResponse("/tasks", status_code=303)

    @rt("/wizard")
    def wizard(step: int = 1):
        return wizard_page(step)

    @rt("/api/wizard/dot", methods=["POST"])
    def wizard_dot(name: str = "", template: str = ""):
        return create_first_dot({"name": name, "template": template})

    @rt("/api/backup")
    def backup(include_models: str = ""):
        from nexora.database.backup import create_backup
        path = create_backup(include_models=bool(include_models))
        return {"ok": True, "archive": path}

    @rt("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        await hub.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            hub.disconnect(websocket)

    @rt("/settings")
    def settings_page():
        channels = [("telegram", TelegramChannel()), ("discord", DiscordChannel()),
                    ("slack", SlackChannel())]
        from nexora.integrations.homeassistant.client import HomeAssistant
        ha = HomeAssistant()
        return shell("Settings",
            Section(H2("System"),
                    P("Host: " + settings.host + ":" + str(settings.port)),
                    P("Local only: " + str(settings.local_only)),
                    P("Auth enabled: " + str(settings.auth_enabled)),
                    P("Data dir: " + str(settings.data_dir)),
                    P("Model dir: " + str(settings.model_dir)),
                    A("Create backup", href="/api/backup"), cls="card"),
            Section(H2("Channels"), *[
                P(n + ": " + ("enabled" if c.enabled() else "not configured"))
                for n, c in channels] + [P("web: enabled")], cls="card"),
            Section(H2("Integrations"),
                    P("Home Assistant: "
                      + ("configured" if ha.configured() else "not configured")),
                    P("MCP: registry available (see docs/MCP.md)"), cls="card"))

    @rt("/api/status")
    def status():
        return {"status": "ready", "local_only": settings.local_only,
                "database": "sqlite",
                "providers": [m.name + ":" + m.status for m in models.available()]}

    return app, rt
