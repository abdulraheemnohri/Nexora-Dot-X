"""FastHTML application: the Nexora control center (HTMX + dark UI)."""
from fasthtml.common import *
from starlette.responses import RedirectResponse

from nexora.config import settings
from nexora.database.engine import init_db
from nexora.database.models import Approval
from nexora.bots.manager import BotManager
from nexora.bots.templates import TEMPLATES
from nexora.core.task_engine import TaskEngine, TaskStatus
from nexora.core.executor import Executor
from nexora.core.events import bus
from nexora.memory.manager import MemoryManager
from nexora.models.router import ModelRouter
from nexora.models.litert.diagnostics import scan, doctor as litert_doctor
from nexora.tools.registry import ToolRegistry
from nexora.tools import terminal as terminal_tool
from nexora.tools import filesystem as fs_tool

NAV = [("Dashboard", "/"), ("Dots", "/dots"), ("Tasks", "/tasks"),
       ("Approvals", "/approvals"), ("Activity", "/activity"),
       ("Models", "/models"), ("Memory", "/memory"), ("Settings", "/settings")]


def shell(title: str, *body):
    nav = Nav(*[A(label, href=href, cls="navlink") for label, href in NAV], cls="nav")
    return Title(f"Nexora Dot X - {title}"), Main(
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
    terminal_tool.register(registry)
    fs_tool.register(registry)
    executor = Executor(tool_registry=registry)

    @rt("/")
    def dashboard():
        running = [t for t in tasks.list() if t.status == TaskStatus.RUNNING.value]
        pending = repo_pending()
        return shell("Dashboard",
            Section(H2("System status"),
                    P(f"Mode: {'LOCAL ONLY' if settings.local_only else 'hybrid'}"),
                    P(f"Active Dots: {sum(1 for d in bots.list() if d.status != 'offline')}"),
                    P(f"Running tasks: {len(running)}"),
                    P(f"Pending approvals: {len(pending)}"),
                    P("Model bus: " + ", ".join(
                        f"{m.name}={m.status}" for m in models.available()) or "none"),
                    cls="card"),
            Section(H2("Recent activity"),
                    *(Li(e.kind) for e in bus.tail(10)) or P("No activity yet."),
                    cls="card"))

    def repo_pending():
        return [a for a in Approval and
                (lambda: [x for x in _approvals() if x.status == 'pending'])()]

    def _approvals():
        from nexora.database import repositories as repo
        return repo.get_all(Approval, limit=100, order_desc="created_at")

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
                    Form(Select(Option(t, value=k) for k, t in
                                [(k, v["name"]) for k, v in TEMPLATES.items()],
                                name="template"),
                         Button("Create from template", cls="btn"),
                         action="/api/dots/template", method="post"), cls="card"),
            Section(H2("Dots"), *[
                Div(H3(f"{d.name} - {d.status}"),
                    P(d.mission or "No mission"),
                    A("start", href=f"/api/dots/{d.id}/start"),
                    " | ", A("pause", href=f"/api/dots/{d.id}/pause"),
                    " | ", A("stop", href=f"/api/dots/{d.id}/stop"),
                    " | ", A("duplicate", href=f"/api/dots/{d.id}/duplicate"),
                    cls="dot-card") for d in items] or P("No Dots yet."), cls="card"))

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
                Div(H3(f"[{t.status}] {t.goal}"),
                    P(f"id {t.id} | dot {t.dot_id}"),
                    P(t.result or t.error or ""),
                    cls="task-card") for t in tasks.list(50)] or P("No tasks."),
                cls="card"))

    @rt("/api/tasks", methods=["POST"])
    async def create_task(goal: str, dot_id: str = ""):
        t = tasks.create(goal, dot_id=dot_id or None)
        from nexora.core.agent import Agent
        dot = bots.get(dot_id) if dot_id else None
        agent = Agent(dot, executor=executor) if dot else None
        if agent is None:
            tasks.set_status(t.id, TaskStatus.QUEUED.value)
        else:
            tasks.set_status(t.id, TaskStatus.QUEUED.value)
            await agent.run_task(t)
        return RedirectResponse("/tasks", status_code=303)

    @rt("/api/tasks/{task_id}/cancel")
    def cancel_task(task_id: str):
        tasks.set_status(task_id, TaskStatus.CANCELLED.value)
        return RedirectResponse("/tasks", status_code=303)

    @rt("/approvals")
    def approvals_page():
        pending = [a for a in _approvals() if a.status == "pending"]
        return shell("Approvals",
            Section(H2("Pending"), *[
                Div(H3(f"{a.tool}: {a.action}"),
                    P(f"risk {a.risk} - {a.reason}"),
                    A("Approve once", href=f"/api/approvals/{a.id}/approve"),
                    " | ", A("Approve always", href=f"/api/approvals/{a.id}/approve?always=1"),
                    " | ", A("Reject", href=f"/api/approvals/{a.id}/reject"),
                    cls="approval-card") for a in pending] or P("No pending approvals."),
                cls="card"))

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
        return shell("Activity",
            Section(H2("Event timeline"),
                    *(Li(f"{e.kind}: {e.payload[:120]}") for e in bus.tail(50))
                    or P("No events yet."), cls="card"))

    @rt("/models")
    def models_page():
        info = scan()
        checks = litert_doctor()
        return shell("Models",
            Section(H2("Model bus"),
                    *(P(f"{m.name}: {m.status} - {m.detail}") for m in models.available()),
                    cls="card"),
            Section(H2("LiteRT-LM"),
                    *(P(c) for c in checks),
                    H3("Installed models"),
                    *(P(f"{m['name']} ({m['size']} bytes, context {m['context']})")
                      for m in info["models"]) or P("No .litertlm models installed."),
                    cls="card"))

    @rt("/memory")
    def memory_page():
        rows = memory.search("")
        return shell("Memory",
            Section(H2("Search"),
                    Form(Input(name="q", placeholder="query"),
                         Button("Search", cls="btn"),
                         action="/memory", method="get"), cls="card"),
            Section(H2("Records"), *[
                Div(P(f"[{r.kind}] {r.content[:160]}"), cls="mem-card")
                for r in rows[:50]] or P("Memory is empty."), cls="card"))

    @rt("/settings")
    def settings_page():
        return shell("Settings",
            Section(H2("System"),
                    P(f"Host: {settings.host}:{settings.port}"),
                    P(f"Local only: {settings.local_only}"),
                    P(f"Auth enabled: {settings.auth_enabled}"),
                    P(f"Data dir: {settings.data_dir}"),
                    P(f"Model dir: {settings.model_dir}"),
                    cls="card"))

    @rt("/api/status")
    def status():
        return {"status": "ready", "local_only": settings.local_only,
                "database": "sqlite"}

    return app, rt
