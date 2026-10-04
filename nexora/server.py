from fasthtml.common import *
from starlette.websockets import WebSocket, WebSocketDisconnect

from nexora.config import settings
from nexora.database.runtime import SessionFactory
from nexora.database.models import Dot
from nexora.core.task_service import TaskService
from nexora.core.planner import Planner
from nexora.core.chat_service import ChatService
from nexora.core.profiles import PROFILES, get_profile
from nexora.control.approvals import ApprovalCenter


def create_app():
    app, rt = fast_app()
    tasks = TaskService(SessionFactory)
    planner = Planner()
    approvals = ApprovalCenter()
    chat = ChatService()

    @rt("/")
    def home():
        return Titled("Nexora Dot X",
                      H1("Nexora Dot X"),
                      P("Local-first autonomous AI control center"),
                      Div(A("Dots", href="/dots"), " · ", A("Chat", href="/chat"),
                          " · ", A("Tasks", href="/tasks"), " · ", A("Approvals", href="/approvals"),
                          " · ", A("Settings", href="/settings")),
                      P(f"Local-only: {settings.local_only} · Profile: {get_profile().name}"))

    @rt("/api/status")
    def status():
        return {"status": "ready", "local_only": settings.local_only,
                "database": "sqlite", "profile": get_profile().name}

    @rt("/chat")
    def chat_page():
        with SessionFactory() as s:
            items = list(s.query(Dot).filter_by(enabled=True).order_by(Dot.created_at.desc()))
        options = [Option(d.name, value=d.id) for d in items] or [Option("No enabled Dots", value="")]
        return Titled("Chat", H1("Chat"),
                      Select(*options, name="dot_id", id="chat-dot"),
                      Div(id="chat-log",
                          hx_ext="ws", ws_connect="/ws/chat",
                          hx_swap="beforeend"),
                      Form(Input(name="message", placeholder="Message", required=True, id="chat-input"),
                           Button("Send"),
                           hx_post="/api/chat", hx_target="#chat-log", hx_swap="beforeend",
                           id="chat-form"),
                      P("Streaming over WebSocket (/ws/chat). Plain replies also work without JS."))

    @rt("/api/chat", methods=["POST"])
    async def api_chat(dot_id: str = "", message: str = ""):
        if not (message or "").strip():
            return P("Empty message.", style="color:#e66")
        reply = chat.reply(dot_id or None, message.strip())
        return Div(P(B("You: "), message), P(B("Dot: "), reply))

    @app.websocket("/ws/chat")
    async def ws_chat(ws: WebSocket):
        await ws.accept()
        dot_id = ws.query_params.get("dot_id") or ""
        try:
            while True:
                message = await ws.receive_text()
                await chat.stream_chat(ws, dot_id, message)
        except WebSocketDisconnect:
            return

    @rt("/dots")
    def dots():
        with SessionFactory() as s:
            items = list(s.query(Dot).order_by(Dot.created_at.desc()))
        return Titled("Dots", H1("Dots"),
                      Form(Input(name="name", placeholder="Dot name", required=True),
                           Input(name="mission", placeholder="Mission"),
                           Button("Create"), action="/api/dots", method="post"),
                      *(Div(H3(d.name), P(d.mission or "No mission"),
                            P("Enabled" if d.enabled else "Paused")) for d in items))

    @rt("/api/dots", methods=["POST"])
    def create_dot(name: str, mission: str = ""):
        import uuid
        with SessionFactory() as s:
            d = Dot(id=uuid.uuid4().hex, name=name, mission=mission)
            s.add(d); s.commit()
        return RedirectResponse("/dots", status_code=303)

    @rt("/tasks")
    def task_page():
        return Titled("Tasks", H1("Tasks"),
                      Form(Input(name="dot_id", placeholder="Dot ID", required=True),
                           Input(name="goal", placeholder="Goal", required=True),
                           Button("Queue task"), action="/api/tasks", method="post"),
                      *(Div(H3(t.goal), P(f"{t.status} · {t.id}")) for t in tasks.list()))

    @rt("/api/tasks", methods=["POST"])
    async def create_task(dot_id: str, goal: str):
        task = await runtime_submit(dot_id, goal)
        return RedirectResponse("/tasks", status_code=303)

    async def runtime_submit(dot_id, goal):
        task = tasks.create(dot_id, goal)
        plan = planner.plan(goal)
        if not plan:
            tasks.set_status(task.id, "FAILED", "Planner returned no steps")
            return task
        tasks.set_status(task.id, "PLANNING")
        tasks.set_status(task.id, "RUNNING")
        tasks.set_status(task.id, "COMPLETED",
                         "Plan created; awaiting configured model/tool execution.")
        return task

    @rt("/approvals")
    def approval_page():
        return Titled("Approvals", H1("Approval Center"),
                      *(Div(H3(a.tool + " · " + a.action), P(a.reason), P(a.status))
                        for a in approvals.pending()) or (P("No pending approvals."),))

    @rt("/api/approvals/{approval_id}/approve", methods=["POST"])
    def approve(approval_id: str):
        approvals.decide(approval_id, True)
        return RedirectResponse("/approvals", status_code=303)

    @rt("/api/approvals/{approval_id}/reject", methods=["POST"])
    def reject(approval_id: str):
        approvals.decide(approval_id, False)
        return RedirectResponse("/approvals", status_code=303)

    @rt("/settings")
    def settings_page():
        active = get_profile().name
        rows = "".join(
            f"<tr><td><b>{name}</b>{' (active)' if name == active else ''}</td>"
            f"<td>{p.max_workers}</td><td>{p.poll_seconds}s</td>"
            f"<td>{'yes' if p.allow_browser else 'no'}</td><td>{p.context}</td></tr>"
            for name, p in PROFILES.items())
        return Titled("Settings", H1("Settings"),
                      H2("Device Profile"),
                      Table(
                          Thead(Th("Profile"), Th("Max workers"), Th("Poll"),
                                Th("Browser"), Th("Context")),
                          Tr(Td(raw(rows))),
                      ),
                      P("Set with NEXORA_PROFILE env var or: nexora start --profile <name>"),
                      H2("System"),
                      P(f"Local-only: {settings.local_only}"),
                      P(f"Auth enabled: {settings.auth_enabled}"),
                      P(f"Host: {settings.host}:{settings.port}"))

    return app
