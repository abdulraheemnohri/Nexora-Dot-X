from fasthtml.common import *
from starlette.websockets import WebSocket, WebSocketDisconnect

from nexora.config import settings
from nexora.database.runtime import SessionFactory
from nexora.database.models import Dot
from nexora.core.task_service import TaskService
from nexora.core.planner import Planner
from nexora.core.chat_service import ChatService
from nexora.core.memory_service import MemoryService
from nexora.core.model_service import ModelService
from nexora.core.profiles import PROFILES, get_profile
from nexora.control.approvals import ApprovalCenter
from nexora.security.auth import AuthManager
from nexora.security.middleware import COOKIE, AuthMiddleware

CHAT_JS = r"""const log = document.getElementById('chat-log');
let dotId = '';
const sel = document.getElementById('chat-dot');
if (sel) { dotId = sel.value; sel.onchange = function() { dotId = sel.value; connect(); }; }
let ws = null;
function addMsg(who, text) {
  const p = document.createElement('p');
  p.innerHTML = '<b>' + who + ':</b> ';
  p.appendChild(document.createTextNode(text));
  log.appendChild(p);
  log.scrollTop = log.scrollHeight;
}
function connect() {
  if (ws) { ws.onclose = null; ws.close(); }
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(proto + '://' + location.host + '/ws/chat?dot_id=' + encodeURIComponent(dotId));
  ws.onmessage = function(ev) {
    const m = JSON.parse(ev.data);
    if (m.kind === 'chat.chunk') { log.lastChild.appendChild(document.createTextNode(m.payload.text)); log.scrollTop = log.scrollHeight; }
    else if (m.kind === 'chat.start') { addMsg('Dot', ''); }
    else if (m.kind === 'chat.error') { addMsg('Error', m.payload.error); }
  };
  ws.onclose = function() { ws = null; };
}
document.getElementById('chat-form').onsubmit = function(ev) {
  ev.preventDefault();
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  addMsg('You', text);
  if (!ws) { connect(); setTimeout(function() { if (ws && ws.readyState === 1) ws.send(text); }, 300); }
  else { ws.send(text); }
  input.value = '';
};
if (window.WebSocket) connect();"""


def create_app():
    app, rt = fast_app()
    tasks = TaskService(SessionFactory)
    planner = Planner()
    approvals = ApprovalCenter()
    chat = ChatService()
    memory = MemoryService()
    models = ModelService()
    auth = AuthManager()

    @rt("/")
    def home():
        ready = models.ready_backend()
        return Titled("Nexora Dot X",
                      H1("Nexora Dot X"),
                      P("Local-first autonomous AI control center"),
                      Div(A("Dots", href="/dots"), " · ", A("Chat", href="/chat"),
                          " · ", A("Memory", href="/memory"), " · ", A("Models", href="/models"),
                          " · ", A("Tasks", href="/tasks"), " · ", A("Approvals", href="/approvals"),
                          " · ", A("Settings", href="/settings")),
                      P("Local-only: " + str(settings.local_only) + " · Profile: " + get_profile().name
                        + " · Model: " + (ready or "none ready")))

    @rt("/api/status")
    def status():
        return {"status": "ready", "local_only": settings.local_only,
                "database": "sqlite", "profile": get_profile().name,
                "model": models.ready_backend()}

    @rt("/login")
    def login_page():
        return Titled("Login", H1("Nexora Login"),
                      Form(Input(name="password", type="password", placeholder="Password", required=True),
                           Button("Login"), action="/auth/login", method="post"),
                      P("Auth is enabled (NEXORA_AUTH_ENABLED=true)."))

    @rt("/auth/login", methods=["POST"])
    def do_login(password: str):
        token = auth.login(password)
        if token is None:
            return RedirectResponse("/login?error=1", status_code=303)
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(COOKIE, token, httponly=True, samesite="lax")
        return resp

    @rt("/auth/logout", methods=["POST"])
    def do_logout():
        resp = RedirectResponse("/login", status_code=303)
        resp.delete_cookie(COOKIE)
        return resp

    @rt("/chat")
    def chat_page():
        with SessionFactory() as s:
            items = list(s.query(Dot).filter_by(enabled=True).order_by(Dot.created_at.desc()))
        options = [Option(d.name, value=d.id) for d in items] or [Option("No enabled Dots", value="")]
        return Titled("Chat", H1("Chat"),
                      Div(H4("Dot: "), Select(*options, id="chat-dot")),
                      Div(id="chat-log", style="border:1px solid #ccc;height:300px;overflow-y:auto;padding:8px"),
                      Form(Input(name="message", placeholder="Message", required=True, id="chat-input"),
                           Button("Send"), id="chat-form"),
                      Script(CHAT_JS))

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

    @rt("/memory")
    def memory_page():
        return Titled("Memory", H1("Memory (federated)"),
                      Form(Input(name="query", placeholder="Search memory...", id="mem-q", autofocus=True),
                           Button("Search"), hx_post="/api/memory/search",
                           hx_target="#mem-results", hx_swap="innerHTML"),
                      Details(Open(False), Summary("Remember something new"),
                              Form(Input(name="content", placeholder="Content", required=True),
                                   Select(Option("semantic", value="semantic"),
                                          Option("user", value="user"),
                                          Option("project", value="project"),
                                          Option("episodic", value="episodic"), name="kind"),
                                   Button("Save"), hx_post="/api/memory/remember",
                                   hx_target="#mem-results", hx_swap="innerHTML")),
                      Div(id="mem-results"))

    @rt("/api/memory/search", methods=["POST"])
    def memory_search(query: str = ""):
        lines = memory.search(query.strip(), limit=100)
        if not lines:
            return P("No memories found.")
        return Ul(*[Li(raw(item.replace("<", "&lt;"))) for item in lines])

    @rt("/api/memory/remember", methods=["POST"])
    def memory_remember(content: str, kind: str = "semantic"):
        ok = memory.remember(content, kind=kind)
        return P("Saved." if ok else "Empty content not saved.",
                 style="color:#4a4" if ok else "color:#e66")

    @rt("/models")
    def models_page():
        rows = "".join(
            "<tr><td>" + m["backend"] + "</td><td>" + m["status"] + "</td>"
            + "<td>" + str(m["model"]) + "</td><td>" + str(m["detail"]) + "</td></tr>"
            for m in models.status())
        ready = models.ready_backend()
        return Titled("Models", H1("Model Management"),
                      P("Active backend: " + (ready or "none ready")),
                      Table(Thead(Th("Backend"), Th("Status"), Th("Model"), Th("Detail")),
                            Tr(Td(raw(rows)))),
                      Button("Scan LiteRT models", hx_post="/api/models/scan",
                             hx_target="#scan-result", hx_swap="innerHTML"),
                      Div(id="scan-result"),
                      P("No model ready? Install one: nexora litert scan / models/gguf / ollama pull"))

    @rt("/api/models/scan", methods=["POST"])
    def models_scan():
        found = models.scan_litert()
        return P("Scan complete: " + str(found) + " LiteRT model(s) found.")

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
            s.add(d)
            s.commit()
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
        await runtime_submit(dot_id, goal)
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
            "<tr><td><b>" + name + "</b>" + (" (active)" if name == active else "") + "</td>"
            + "<td>" + str(p.max_workers) + "</td><td>" + str(p.poll_seconds) + "s</td>"
            + "<td>" + ("yes" if p.allow_browser else "no") + "</td>"
            + "<td>" + str(p.context) + "</td></tr>"
            for name, p in PROFILES.items())
        return Titled("Settings", H1("Settings"),
                      H2("Device Profile"),
                      Table(Thead(Th("Profile"), Th("Max workers"), Th("Poll"),
                                  Th("Browser"), Th("Context")), Tr(Td(raw(rows)))),
                      P("Set with NEXORA_PROFILE env var or: nexora start --profile <name>"),
                      H2("System"),
                      P("Local-only: " + str(settings.local_only)),
                      P("Auth enabled: " + str(settings.auth_enabled)),
                      P("Host: " + str(settings.host) + ":" + str(settings.port)),
                      Form(Button("Logout"), action="/auth/logout", method="post"))

    app = AuthMiddleware(app)
    return app
