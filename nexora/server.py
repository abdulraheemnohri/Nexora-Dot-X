from time import time

from fasthtml.common import *
from starlette.websockets import WebSocket, WebSocketDisconnect

from nexora import __version__
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
from nexora.control import always_allow as grants_store
from nexora.security.auth import AuthManager
from nexora.security.middleware import COOKIE, AuthMiddleware
from nexora.skills.manager import SkillManager
from nexora.skills.scanner import scan_skill_files

CHAT_JS = r"""const log = document.getElementById('chat-log');
let dotId = '';
const sel = document.getElementById('chat-dot');
if (sel) { dotId = sel.value;
  sel.onchange = function() { dotId = sel.value; connect(); }; }
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
  const u = proto + '://' + location.host + '/ws/chat?dot_id='
      + encodeURIComponent(dotId);
  ws = new WebSocket(u);
  ws.onmessage = function(ev) {
    const m = JSON.parse(ev.data);
    if (m.kind === 'chat.chunk') {
      log.lastChild.appendChild(
          document.createTextNode(m.payload.text));
      log.scrollTop = log.scrollHeight;
    } else if (m.kind === 'chat.start') { addMsg('Dot', ''); }
    else if (m.kind === 'chat.error') {
      addMsg('Error', m.payload.error);
    }
  };
  ws.onclose = function() { ws = null; };
}
document.getElementById('chat-form').onsubmit = function(ev) {
  ev.preventDefault();
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  addMsg('You', text);
  if (!ws) {
    connect();
    setTimeout(function() {
      if (ws && ws.readyState === 1) ws.send(text);
    }, 300);
  } else { ws.send(text); }
  input.value = '';
};
if (window.WebSocket) connect();"""

START_TIME = time()


def create_app():
    app, rt = fast_app()
    tasks = TaskService(SessionFactory)
    planner = Planner()
    approvals = ApprovalCenter()
    chat = ChatService()
    memory = MemoryService()
    models = ModelService()
    auth = AuthManager()
    skills = SkillManager()

    @rt("/")
    def home():
        ready = models.ready_backend()
        return Titled("Nexora Dot X",
                      H1("Nexora Dot X"),
                      P("Local-first autonomous AI control center"),
                      Div(A("Dots", href="/dots"), " · ",
                          A("Chat", href="/chat"), " · ",
                          A("Memory", href="/memory"), " · ",
                          A("Models", href="/models"), " · ",
                          A("Skills", href="/skills"), " · ",
                          A("Tasks", href="/tasks"), " · ",
                          A("Approvals", href="/approvals"), " · ",
                          A("Settings", href="/settings")),
                      P("Local-only: " + str(settings.local_only)
                        + " · Profile: " + get_profile().name
                        + " · Model: " + (ready or "none ready")))

    @rt("/api/status")
    def status():
        return {"status": "ready",
                "version": __version__,
                "local_only": settings.local_only,
                "auth_enabled": settings.auth_enabled,
                "database": "sqlite",
                "profile": get_profile().name,
                "uptime_seconds": round(time() - START_TIME, 1),
                "model": models.ready_backend(),
                "models": [{"backend": m["backend"],
                            "status": m["status"],
                            "model": m["model"]}
                           for m in models.status()],
                "pending_approvals": len(approvals.pending()),
                "always_allow_grants": len(grants_store.list_grants()),
                "pending_skills": len(skills.pending())}

    @rt("/login")
    def login_page():
        return Titled("Login", H1("Nexora Login"),
                      Form(Input(name="password", type="password",
                                 placeholder="Password", required=True),
                           Button("Login"), action="/auth/login",
                           method="post"),
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
            items = list(s.query(Dot).filter_by(enabled=True)
                         .order_by(Dot.created_at.desc()))
        options = [Option(d.name, value=d.id) for d in items]
        if not options:
            options = [Option("No enabled Dots", value="")]
        return Titled("Chat", H1("Chat"),
                      Div(H4("Dot: "), Select(*options, id="chat-dot")),
                      Div(id="chat-log",
                          style="border:1px solid #ccc;height:300px;"
                                "overflow-y:auto;padding:8px"),
                      Form(Input(name="message", placeholder="Message",
                                 required=True, id="chat-input"),
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
                      Form(Input(name="query", placeholder="Search memory...",
                                 id="mem-q", autofocus=True),
                           Button("Search"), hx_post="/api/memory/search",
                           hx_target="#mem-results", hx_swap="innerHTML"),
                      Details(Open(False), Summary("Remember something new"),
                              Form(Input(name="content", placeholder="Content",
                                         required=True),
                                   Select(Option("semantic", value="semantic"),
                                          Option("user", value="user"),
                                          Option("project", value="project"),
                                          Option("episodic", value="episodic"),
                                          name="kind"),
                                   Button("Save"), hx_post="/api/memory/remember",
                                   hx_target="#mem-results",
                                   hx_swap="innerHTML")),
                      Div(id="mem-results"))

    @rt("/api/memory/search", methods=["POST"])
    def memory_search(query: str = ""):
        hits = memory.search_detailed(query.strip(), limit=100)
        if not hits:
            return P("No memories found.")
        items = []
        for h in hits:
            badge = ""
            kind = h.get("kind")
            if kind:
                color = {"user": "#06c", "semantic": "#4a4",
                         "project": "#a60", "episodic": "#555"}.get(kind,
                                                                    "#999")
                badge = (" <small style='color:" + color + "'>["
                         + str(kind) + "]</small>")
            conf = h.get("confidence")
            if conf is not None:
                badge += (" <small style='color:#999'>conf "
                          + str(conf) + "</small>")
            content = str(h.get("content", "")).replace("<", "&lt;")
            items.append("<li>" + content + badge + "</li>")
        return Ul(raw("".join(items)))

    @rt("/api/memory/remember", methods=["POST"])
    def memory_remember(content: str, kind: str = "semantic"):
        ok = memory.remember(content, kind=kind)
        style = "color:#4a4" if ok else "color:#e66"
        return P("Saved." if ok else "Empty content not saved.",
                 style=style)

    # ---- models ------------------------------------------------------------

    def _model_rows():
        rows = ""
        for m in models.status():
            rows += ("<tr><td>" + m["backend"] + "</td><td>"
                     + m["status"] + "</td><td>"
                     + str(m["model"]).replace("<", "&lt;")
                     + "</td><td>"
                     + str(m["detail"]).replace("<", "&lt;")
                     + "</td><td>")
            if m["status"] == "ready":
                rows += ("<form hx_post='/api/models/unload' "
                         "hx_target='#models-result' "
                         "hx_swap='innerHTML'>"
                         "<input type='hidden' name='backend' value='"
                         + m["backend"] + "'>"
                         "<button>Unload</button></form>")
            else:
                rows += ("<form hx_post='/api/models/load' "
                         "hx_target='#models-result' "
                         "hx_swap='innerHTML'>"
                         "<input type='hidden' name='backend' value='"
                         + m["backend"]
                         + "'><input name='name' "
                         "placeholder='model name/path'>"
                         "<button>Load</button></form>")
            rows += "</td></tr>"
        return rows

    @rt("/models")
    def models_page():
        ready = models.ready_backend()
        return Titled("Models", H1("Model Management"),
                      P("Active backend: " + (ready or "none ready")),
                      Table(Thead(Th("Backend"), Th("Status"),
                                  Th("Model"), Th("Detail"), Th("Action")),
                            Tr(Td(raw(_model_rows())))),
                      Div(id="models-result"),
                      H2("Discover"),
                      Button("Find models", hx_post="/api/models/discover",
                             hx_target="#discover-result",
                             hx_swap="innerHTML"),
                      Div(id="discover-result"),
                      P("No model ready? Install one: "
                        "nexora litert install / models/gguf / ollama pull"))

    @rt("/api/models/scan", methods=["POST"])
    def models_scan():
        found = models.scan_litert()
        return P("Scan complete: " + str(found)
                 + " LiteRT model(s) found.")

    @rt("/api/models/load", methods=["POST"])
    def models_load(backend: str, name: str = ""):
        if not (name or "").strip():
            return P("Enter a model name or path to load.",
                     style="color:#e66")
        r = models.load(backend, name.strip())
        if not r.get("ok"):
            return P("Load failed: "
                     + str(r.get("error", "unknown error")),
                     style="color:#e66")
        return P("Loaded on " + str(r.get("backend")) + ": "
                 + str(r.get("model")) + " (" + str(r.get("status"))
                 + ")", style="color:#4a4")

    @rt("/api/models/unload", methods=["POST"])
    def models_unload(backend: str):
        r = models.unload(backend)
        if not r.get("ok"):
            return P("Unload failed: "
                     + str(r.get("error", "unknown error")),
                     style="color:#e66")
        return P("Unloaded " + str(r.get("backend")) + " ("
                 + str(r.get("status")) + ")",
                 style="color:#4a4")

    @rt("/api/models/discover", methods=["POST"])
    def models_discover():
        entries = models.discover()
        if not entries:
            return P("No model backends registered.")
        items = []
        for e in entries:
            names = e.get("models") or []
            if names:
                listing = ", ".join(str(n) for n in names[:10])
                items.append("<li><b>" + e["backend"] + "</b>: "
                             + listing.replace("<", "&lt;") + "</li>")
        if not items:
            return P("No loadable models found. Drop a .litertlm/.gguf "
                     "in models/ or pull an Ollama model.")
        return Ul(raw("".join(items)))
