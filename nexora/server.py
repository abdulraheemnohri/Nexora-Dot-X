from time import time

from fasthtml.common import *
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.datastructures import UploadFile

from nexora import __version__
from nexora.config import settings
from nexora.database.runtime import SessionFactory
from nexora.database.models import Dot, Task
from nexora.core.task_engine import TaskEngine
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
from nexora.skills.runtime import run_skill
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

TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}
PAGE_SIZE = 20
MEMORY_PAGE_SIZE = 20


def create_app():
    app, rt = fast_app()
    tasks = TaskEngine()
    planner = Planner()
    approvals = ApprovalCenter()
    chat = ChatService()
    memory = MemoryService()
    models = ModelService()
    auth = AuthManager()
    skills = SkillManager()

    @rt("/")
    def home():
        pending_approvals = len(approvals.pending())
        return Titled("Nexora Dot X",
                      H1("Nexora Dot X"),
                      P("Local-first autonomous AI control center"),
                      Div(A("Dots", href="/dots"), " · ",
                          A("Chat", href="/chat"), " · ",
                          A("Memory", href="/memory"), " · ",
                          A("Models", href="/models"), " · ",
                          A("Skills", href="/skills"), " · ",
                          A("Tasks", href="/tasks"), " · ",
                          A("Approvals"
                            + ((" (" + str(pending_approvals) + ")")
                               if pending_approvals else ""),
                            href="/approvals"), " · ",
                          A("Settings", href="/settings")),
                      H2("Live status"),
                      Div(id="status-live",
                          hx_get="/api/status/card",
                          hx_trigger="load, every 5s",
                          hx_swap="innerHTML"))

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

    @rt("/api/status/card")
    def status_card():
        """HTML fragment for the home live dashboard (HTMX polling)."""
        ready = models.ready_backend()
        rows = ""
        for m in models.status():
            rows += ("<tr><td>" + m["backend"] + "</td><td>"
                     + m["status"] + "</td><td>"
                     + str(m["model"]).replace("<", "&lt;")
                     + "</td></tr>")
        uptime = round(time() - START_TIME, 0)
        html = (
            "<p>Version: " + __version__
            + " · Profile: " + get_profile().name
            + " · Uptime: " + str(int(uptime // 60)) + "m "
            + str(int(uptime % 60)) + "s</p>"
            "<p>Local-only: " + str(settings.local_only)
            + " · Auth: " + str(settings.auth_enabled)
            + " · Model: " + (ready or "none ready") + "</p>"
            "<p>Pending approvals: " + str(len(approvals.pending()))
            + " · Always-allow grants: "
            + str(len(grants_store.list_grants()))
            + " · Pending skills: " + str(len(skills.pending())) + "</p>")
        with SessionFactory() as s:
            dots = list(s.query(Dot).order_by(Dot.created_at.desc()))
        if dots:
            dot_html = ""
            for d in dots:
                state = "enabled" if d.enabled else "paused"
                label = "Pause" if d.enabled else "Resume"
                dot_html += (
                    "<li>" + str(d.name).replace("<", "&lt;")
                    + " <small>[" + state + "]</small>"
                    + ' <form method="post" action="/api/dots/toggle">'
                    + '<input type="hidden" name="dot_id" value="'
                    + str(d.id) + '">'
                    + "<button>" + label + "</button></form></li>")
            html += ("<h3>Dots</h3><ul>" + dot_html + "</ul>")
        if rows:
            html += ("<table><tr><th>Backend</th><th>Status</th>"
                     "<th>Model</th></tr>" + rows + "</table>")
        return raw(html)

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
                                 id="mem-q", autofocus=True,
                                 hx_get="/api/memory/rows",
                                 hx_trigger="keyup changed delay:400ms, search",
                                 hx_target="#mem-live", hx_swap="innerHTML"),
                           Button("Search"), hx_post="/api/memory/search",
                           hx_target="#mem-results", hx_swap="innerHTML"),
                      Div(id="mem-live"),
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

    @rt("/api/memory/rows")
    def memory_rows(query: str = "", page: int = 1):
        """Live search fragment: debounced memory search (HTMX)."""
        query = (query or "").strip()
        if not query:
            return P("Type to search memories (live).",
                     style="color:#999")
        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1
        hits = memory.search_detailed(query, limit=100)
        total = len(hits)
        pages = max(1, (total + MEMORY_PAGE_SIZE - 1) // MEMORY_PAGE_SIZE)
        hits = hits[(page - 1) * MEMORY_PAGE_SIZE:
                    page * MEMORY_PAGE_SIZE]
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
            text = str(h.get("content", "")).replace("<", "&lt;")
            items.append("<li>" + text + badge + "</li>")
        nav = ""
        if pages > 1:
            for p in range(1, pages + 1):
                if p == page:
                    nav += " <b>[" + str(p) + "]</b>"
                else:
                    nav += (' <a href="/api/memory/rows?query='
                            + query.replace(" ", "%20")
                            + "&page=" + str(p) + '">'
                            + str(p) + "</a>")
        return Div(Ul(raw("".join(items))), raw(nav))

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
                      Div(id="models-live",
                          hx_get="/api/models/rows",
                          hx_trigger="load, every 5s",
                          hx_swap="innerHTML"),
                      Div(id="models-result"),
                      H2("Discover"),
                      Button("Find models", hx_post="/api/models/discover",
                             hx_target="#discover-result",
                             hx_swap="innerHTML"),
                      Div(id="discover-result"),
                      P("No model ready? Install one: "
                        "nexora litert install / models/gguf / ollama pull"))

    @rt("/api/models/rows")
    def models_rows():
        return raw("<table><tr><th>Backend</th><th>Status</th>"
                   "<th>Model</th><th>Detail</th><th>Action</th></tr>"
                   + _model_rows() + "</table>")

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

    # ---- skills ------------------------------------------------------------

    @rt("/skills")
    def skills_page():
        pending = skills.pending()
        active = skills.scan()
        pend_rows = ""
        for s in pending:
            sc = scan_skill_files(s)
            if sc["ok"]:
                finding = ("clean (" + str(sc["files_scanned"])
                           + " file(s))")
            else:
                finding = ("<span style='color:#e66'>"
                           + "; ".join(sc["issues"])[:200]
                           .replace("<", "&lt;") + "</span>")
            pend_rows += (
                "<tr><td>" + str(s.get("name", "?")) + "</td><td>"
                + str(s.get("description", "")) + "</td><td>"
                + finding + "</td><td>"
                + '<form hx_post="/api/skills/approve" '
                + 'hx_target="#skills-result" hx_swap="innerHTML">'
                + '<input type="hidden" name="name" value="'
                + str(s.get("name", "")) + '"><button>Approve</button></form>'
                + "</td><td>"
                + '<form hx_post="/api/skills/reject" '
                + 'hx_target="#skills-result" hx_swap="innerHTML">'
                + '<input type="hidden" name="name" value="'
                + str(s.get("name", "")) + '"><button>Reject</button></form>'
                + "</td><td>"
                + '<form hx_post="/api/skills/scan" '
                + 'hx_target="#skills-result" hx_swap="innerHTML">'
                + '<input type="hidden" name="name" value="'
                + str(s.get("name", "")) + '"><button>Scan</button></form>'
                + "</td><td>"
                + '<form hx_post="/api/skills/detail" '
                + 'hx_target="#skills-result" hx_swap="innerHTML">'
                + '<input type="hidden" name="name" value="'
                + str(s.get("name", "")) + '"><button>Detail</button></form>'
                + "</td></tr>")
        act_rows = ""
        for s in active:
            sc = scan_skill_files(s)
            if sc["ok"]:
                scan_note = ("clean (" + str(sc["files_scanned"])
                             + " file(s))")
            else:
                scan_note = ("<span style='color:#e66'>"
                             + "; ".join(sc["issues"])[:200]
                             .replace("<", "&lt;") + "</span>")
            act_rows += (
                "<tr><td>" + str(s.get("name", "?")) + "</td><td>"
                + str(s.get("description", "")) + "</td><td>active</td><td>"
                + scan_note + "</td><td>"
                + '<form hx_post="/api/skills/run" '
                + 'hx_target="#skills-result" hx_swap="innerHTML">'
                + '<input type="hidden" name="name" value="'
                + str(s.get("name", "")) + '">'
                + '<input name="payload" placeholder="input text">'
                + "<button>Run</button></form>"
                + "</td><td>"
                + '<form hx_post="/api/skills/scan" '
                + 'hx_target="#skills-result" hx_swap="innerHTML">'
                + '<input type="hidden" name="name" value="'
                + str(s.get("name", "")) + '"><button>Scan</button></form>'
                + "</td><td>"
                + '<form hx_post="/api/skills/detail" '
                + 'hx_target="#skills-result" hx_swap="innerHTML">'
                + '<input type="hidden" name="name" value="'
                + str(s.get("name", "")) + '"><button>Detail</button></form>'
                + "</td></tr>")
        return Titled("Skills", H1("Skills"),
                      Details(Open(False),
                              Summary("Import a skill (.zip)"),
                              Form(Input(type="file", name="file",
                                         required=True, accept=".zip"),
                                   Button("Upload"),
                                   hx_post="/api/skills/upload",
                                   hx_encoding="multipart/form-data",
                                   hx_target="#skills-result",
                                   hx_swap="innerHTML")),
                      H2("Pending approval"),
                      (Table(Thead(Th("Name"), Th("Description"),
                                   Th("Static scan"), Th(""), Th(""),
                                   Th(""), Th("")),
                             Tr(Td(raw(pend_rows))))
                       if pending
                       else P("No skills awaiting approval.")),
                      H2("Active skills"),
                      (Table(Thead(Th("Name"), Th("Description"),
                                   Th("Status"), Th("Static scan"),
                                   Th("Run"), Th(""), Th("")),
                             Tr(Td(raw(act_rows))))
                       if active else P("No active skills yet.")),
                      P(A("Export skills (JSON)",
                          href="/api/skills/export")),
                      P("Self-grown skills require explicit user approval - "
                        "the AI cannot activate them (System 1). Only "
                        "approved skills can be run; the static scan is "
                        "re-checked before every execution."),
                      Div(id="skills-result"))

    @rt("/api/skills/upload", methods=["POST"])
    async def skills_upload(file: UploadFile):
        """Import a skill .zip: safe unpack, static scan, then
        queue it for approval (never auto-activated)."""
        import shutil
        import tempfile
        import zipfile
        from pathlib import Path

        if (file is None or not file.filename
                or not file.filename.endswith(".zip")):
            return P("Please choose a .zip archive.",
                     style="color:#e66")
        tmp = Path(tempfile.mkdtemp(prefix="nexora-skill-"))
        try:
            zip_path = tmp / "upload.zip"
            zip_path.write_bytes(await file.read())
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    bad = [n for n in zf.namelist()
                           if n.startswith(("/", "\\")) or ".." in n]
                    if bad:
                        return P("Unsafe path in archive: "
                                 + bad[0], style="color:#e66")
                    zf.extractall(tmp / "unpacked")
            except zipfile.BadZipFile:
                return P("Not a valid .zip archive.",
                         style="color:#e66")
            meta_files = sorted((tmp / "unpacked").rglob("skill.json"))
            if not meta_files:
                return P("No skill.json found inside the archive.",
                         style="color:#e66")
            skill_dir = meta_files[0].parent
            sc = scan_skill_files({"_dir": str(skill_dir)})
            if not sc["ok"]:
                issues = ("; ".join(sc["issues"])[:300]
                          .replace("<", "&lt;"))
                return P("Static scan failed - nothing imported: "
                         + issues, style="color:#e66")
            r = skills.install_from_dir(skill_dir)
            if not r.get("ok"):
                return P("Import failed: " + str(r.get("error")),
                         style="color:#e66")
            return P("Skill submitted for approval: "
                     + str(r.get("skill")) + " (static scan clean, "
                     + str(sc["files_scanned"]) + " file(s) scanned).",
                     style="color:#4a4")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    @rt("/api/skills")
    def api_skills():
        """Machine-readable skill list for integrations."""
        def _clean(entries):
            out = []
            for s in entries:
                item = {k: v for k, v in s.items()
                        if not str(k).startswith("_")}
                sc = scan_skill_files(s)
                item["static_scan_ok"] = sc["ok"]
                item["static_scan_issues"] = sc["issues"]
                item["files_scanned"] = sc["files_scanned"]
                out.append(item)
            return out
        return {"active": _clean(skills.scan()),
                "pending": _clean(skills.pending())}

    @rt("/api/skills/export")
    def skills_export():
        """Export all skills (active + pending) as JSON."""
        def _plain(entries):
            return [{k: v for k, v in s.items()
                     if not str(k).startswith("_")}
                    for s in entries]
        return {"active": _plain(skills.scan()),
                "pending": _plain(skills.pending())}

    @rt("/api/skills/approve", methods=["POST"])
    def skill_approve(name: str):
        r = skills.approve(name)
        style = "color:#4a4" if r["ok"] else "color:#e66"
        text = ("Skill approved: " + name if r["ok"]
                else "Error: " + r.get("error", ""))
        return P(text, style=style)

    @rt("/api/skills/reject", methods=["POST"])
    def skill_reject(name: str):
        r = skills.reject(name)
        text = ("Skill rejected: " + name if r["ok"]
                else "Error: " + r.get("error", ""))
        return P(text, style="color:#e66")

    @rt("/api/skills/scan", methods=["POST"])
    def skill_scan(name: str):
        s = skills.inspect(name)
        if not s:
            return P("Skill not found: " + name, style="color:#e66")
        r = scan_skill_files(s)
        if r["ok"]:
            return P("Scan clean for " + name + " ("
                     + str(r["files_scanned"]) + " file(s)).",
                     style="color:#4a4")
        items = "".join("<li>" + i.replace("<", "&lt;") + "</li>"
                       for i in r["issues"])
        return Div(P("Findings for " + name + ":", style="color:#e66"),
                   Ul(raw(items)))

    @rt("/api/skills/detail", methods=["POST"])
    def skill_detail(name: str):
        s = skills.inspect(name)
        if not s:
            return P("Skill not found: " + name, style="color:#e66")
        meta = {k: v for k, v in s.items()
                if not str(k).startswith("_")}
        meta_rows = "".join(
            "<tr><td>" + str(k).replace("<", "&lt;") + "</td><td>"
            + str(v).replace("<", "&lt;") + "</td></tr>"
            for k, v in sorted(meta.items()))
        html = "<h3>Skill: " + str(s.get("name", name)) + "</h3>"
        if meta_rows:
            html += ("<table><tr><th>Field</th><th>Value</th></tr>"
                     + meta_rows + "</table>")
        sc = scan_skill_files(s)
        if sc["ok"]:
            html += ("<p style='color:#4a4'>Static scan: clean ("
                     + str(sc["files_scanned"]) + " file(s))</p>")
        else:
            items = "".join("<li>" + i.replace("<", "&lt;") + "</li>"
                            for i in sc["issues"])
            html += ("<p style='color:#e66'>Static scan findings:</p>"
                     "<ul>" + items + "</ul>")
        skill_dir = s.get("_dir") or ""
        files = ""
        if skill_dir:
            from pathlib import Path
            d = Path(skill_dir)
            if d.exists():
                for f in sorted(d.glob("**/*")):
                    if f.is_file():
                        size = f.stat().st_size
                        files += ("<li>"
                                  + f.relative_to(d).as_posix()
                                  + " (" + str(size) + " bytes)</li>")
        if files:
            html += "<h4>Files</h4><ul>" + files + "</ul>"
        return raw(html)

    @rt("/api/skills/run", methods=["POST"])
    def skill_run(name: str, payload: str = ""):
        s = skills.inspect(name)
        if not s:
            return P("Skill not found: " + name, style="color:#e66")
        r = run_skill(s, payload)
        if not r.get("ok"):
            return P("Run failed: "
                     + str(r.get("error", "unknown error")),
                     style="color:#e66")
        return P("Result: " + str(r.get("result")).replace("<", "&lt;"),
                 style="color:#4a4")

    # ---- dots ---------------------------------------------------------------

    @rt("/dots")
    def dots():
        with SessionFactory() as s:
            items = list(s.query(Dot).order_by(Dot.created_at.desc()))
        return Titled("Dots", H1("Dots"),
                      Form(Input(name="name", placeholder="Dot name",
                                 required=True),
                           Input(name="mission", placeholder="Mission"),
                           Button("Create"), action="/api/dots",
                           method="post"),
                      *(Div(H3(d.name),
                            P(d.mission or "No mission"),
                            P(("Enabled" if d.enabled else "Paused")
                               + " · " + d.id),
                            Form(Button(("Pause" if d.enabled
                                         else "Resume")),
                                 Input(type="hidden", name="dot_id",
                                       value=d.id),
                                 action="/api/dots/toggle",
                                 method="post"),
                            P(A("View details", href="/dots/" + d.id)))
                        for d in items))

    @rt("/dots/{dot_id}")
    def dot_detail(dot_id: str):
        """Dot detail: profile, queue-task form and all of its tasks."""
        with SessionFactory() as s:
            d = s.get(Dot, dot_id)
            if d is None:
                return Titled("Dot", H1("Dot not found: " + dot_id))
        rows = "".join(
            "<tr><td>" + k + "</td><td>"
            + str(v).replace("<", "&lt;") + "</td></tr>"
            for k, v in [("ID", d.id), ("Name", d.name),
                         ("Mission", d.mission or ""),
                         ("Description", d.description or ""),
                         ("Personality", d.personality or ""),
                         ("Model", d.model or ""),
                         ("Status", d.status or ""),
                         ("Enabled", "yes" if d.enabled else "no"),
                         ("Workspace", d.workspace or ""),
                         ("Created", d.created_at)])
        return Titled("Dot", H1(d.name),
                      Table(Thead(Th("Field"), Th("Value")),
                            Tr(Td(raw(rows)))),
                      H2("Queue a task"),
                      Form(Input(type="hidden", name="dot_id",
                                 value=d.id),
                           Input(name="goal", placeholder="Goal",
                                 required=True),
                           Button("Queue task"), action="/api/tasks",
                           method="post"),
                      H2("Tasks"),
                      Div(id="dot-tasks-live",
                          hx_get="/api/dots/" + dot_id + "/tasks/rows",
                          hx_trigger="load, every 5s",
                          hx_swap="innerHTML"),
                      P(A("Back to Dots", href="/dots")))

    @rt("/api/dots", methods=["POST"])
    def create_dot(name: str, mission: str = ""):
        import uuid
        with SessionFactory() as s:
            d = Dot(id=uuid.uuid4().hex, name=name, mission=mission)
            s.add(d)
            s.commit()
        return RedirectResponse("/dots", status_code=303)

    @rt("/api/dots/{dot_id}/tasks/rows")
    def dot_tasks_rows(dot_id: str):
        """Live tasks fragment for one Dot (HTMX polling)."""
        with SessionFactory() as s:
            d = s.get(Dot, dot_id)
            if d is None:
                return P("Dot not found: " + dot_id,
                         style="color:#e66")
            task_rows = list(s.query(Task)
                             .filter_by(dot_id=dot_id)
                             .order_by(Task.created_at.desc()))
        if not task_rows:
            return P("No tasks for this Dot yet.")
        items = ""
        for t in task_rows:
            goal = str(t.goal).replace("<", "&lt;")
            items += ("<li>[" + str(t.status) + "] " + goal
                      + " · " + str(t.id) + "</li>")
        return Ul(raw(items))

    @rt("/api/dots/toggle", methods=["POST"])
    def toggle_dot(dot_id: str):
        """Enable/pause a Dot (paused Dots stop receiving new work)."""
        with SessionFactory() as s:
            d = s.get(Dot, dot_id)
            if d is None:
                return P("Dot not found: " + dot_id, style="color:#e66")
            d.enabled = not d.enabled
            s.commit()
        return RedirectResponse("/dots", status_code=303)

    # ---- tasks --------------------------------------------------------------

    def _task_filter_links(current: str = "", dot_id: str = ""):
        def _qs(status, dot):
            q = ""
            if status:
                q += "?status=" + status
            if dot:
                q += ("&" if q else "?") + "dot=" + dot
            return q

        def _link(label, value):
            href = "/tasks" + _qs(value, dot_id)
            shown = "[" + label + "]" if value == current else label
            return A(shown, href=href)

        return Div(
            _link("All", ""),
            " · ",
            _link("RUNNING", "RUNNING"),
            " · ",
            _link("COMPLETED", "COMPLETED"),
            " · ",
            _link("FAILED", "FAILED"),
            " · ",
            _link("CANCELLED", "CANCELLED"))

    @rt("/tasks")
    def task_page(status: str = "", dot: str = ""):
        with SessionFactory() as s:
            all_dots = list(s.query(Dot).order_by(
                Dot.created_at.desc()))
        dot_options = '<option value="">All dots</option>'
        for d in all_dots:
            selected = (" selected" if str(d.id) == (dot or "")
                        else "")
            dot_options += ('<option value="' + str(d.id) + '"'
                            + selected + ">"
                            + str(d.name).replace("<", "&lt;")
                            + " (id " + str(d.id) + ")</option>")
        return Titled("Tasks", H1("Tasks"),
                      Form(Input(name="dot_id", placeholder="Dot ID",
                                 required=True),
                           Input(name="goal", placeholder="Goal",
                                 required=True),
                           Button("Queue task"), action="/api/tasks",
                           method="post"),
                      H2("Filter"),
                      _task_filter_links(status, dot),
                      raw('<form method="get" action="/tasks">'
                          + '<input type="hidden" name="status" value="'
                          + str(status or "") + '">'
                          + '<select name="dot">' + dot_options
                          + '</select>'
                          + '<button>Filter by dot</button></form>'),
                      H2("Tasks"),
                      Div(id="tasks-live",
                          hx_get="/api/tasks/rows"
                          + (("?status=" + status) if status else "")
                          + ((("&dot=" + dot) if status else ("?dot=" + dot))
                             if dot else ""),
                          hx_trigger="load, every 5s",
                          hx_swap="innerHTML"),
                      Div(id="tasks-result"))

    @rt("/api/tasks/rows")
    def tasks_rows(status: str = "", dot: str = "", page: int = 1):
        """Live task table fragment (HTMX polling every 5s).

        Optional ?status= filter narrows the list to one status.
        Optional ?page= selects a 20-task page (1-based).
        Non-terminal tasks get an inline Cancel button.
        """
        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1
        all_tasks = tasks.list(status=(status or None),
                                 dot_id=(dot or None))
        total = len(all_tasks)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        start = (page - 1) * PAGE_SIZE
        page_tasks = all_tasks[start:start + PAGE_SIZE]
        rows = ""
        for t in page_tasks:
            goal = str(t.goal).replace("<", "&lt;")
            rows += ("<tr><td>" + goal + "</td><td>"
                     + str(t.status) + "</td><td>"
                     + str(t.id) + "</td><td>"
                     + '<form hx_post="/api/tasks/detail" '
                     + 'hx_target="#tasks-result" hx_swap="innerHTML">'
                     + '<input type="hidden" name="task_id" value="'
                     + str(t.id) + '"><button>Detail</button></form>'
                     + "</td><td>")
            if str(t.status) not in TERMINAL_STATUSES:
                rows += ('<form hx_post="/api/tasks/cancel" '
                         'hx_target="#tasks-result" '
                         'hx_swap="innerHTML">'
                         '<input type="hidden" name="task_id" value="'
                         + str(t.id) + '"><button>Cancel</button></form>')
            rows += "</td></tr>"
        if not rows:
            return P("No tasks"
                     + ((" with status " + status) if status else "")
                     + ".")
        nav = ""
        if pages > 1:
            links = ""
            for p in range(1, pages + 1):
                href = ("/api/tasks/rows?page=" + str(p)
                        + (("&status=" + status) if status else "")
                        + (("&dot=" + dot) if dot else ""))
                if p == page:
                    links += " <b>[" + str(p) + "]</b>"
                else:
                    links += (' <a href="' + href + '" hx_get="'
                              + href + '" hx_target="#tasks-live" '
                              'hx_swap="innerHTML">' + str(p) + "</a>")
            nav = ("<p>Page " + str(page) + " of " + str(pages)
                   + ": " + links.strip() + "</p>")
        return raw("<table><tr><th>Goal</th><th>Status</th><th>ID</th>"
                   "<th></th><th></th></tr>" + rows + "</table>" + nav)

    @rt("/api/tasks/detail", methods=["POST"])
    def task_detail(task_id: str):
        """Show one task: goal, status, plan steps, result, error."""
        t = tasks.get(task_id)
        if t is None:
            return P("Task not found: " + task_id, style="color:#e66")
        plan = tasks.get_plan(t) or []
        n_steps = len(plan)
        plan_items = ""
        for idx, step in enumerate(plan, start=1):
            plan_items += ("<li><b>Step " + str(idx) + "/" + str(n_steps) + "</b> - "
                           + str(step).replace("<", "&lt;")
                           + "</li>")
        rows = "".join(
            "<tr><td>" + k + "</td><td>"
            + str(v).replace("<", "&lt;") + "</td></tr>"
            for k, v in [
                ("ID", t.id),
                ("Dot", t.dot_id),
                ("Goal", t.goal),
                ("Status", t.status),
                ("Priority", t.priority),
                ("Result", t.result or ""),
                ("Error", t.error or ""),
                ("Created", t.created_at),
                ("Updated", t.updated_at)])
        html = ("<h3>Task: " + str(t.goal).replace("<", "&lt;")
                 + "</h3>"
                 "<table><tr><th>Field</th><th>Value</th></tr>"
                 + rows + "</table>")
        html += ("<h4>Plan (" + str(n_steps) + " step(s), status: "
                 + str(t.status) + ")</h4>")
        if plan_items:
            html += "<ol>" + plan_items + "</ol>"
        else:
            html += P("No plan steps recorded.")
        return raw(html)

    @rt("/api/tasks/cancel", methods=["POST"])
    def task_cancel(task_id: str):
        """Cancel a task (sets status to CANCELLED)."""
        t = tasks.set_status(task_id, "CANCELLED",
                             result="Cancelled by user")
        if t is None:
            return P("Task not found: " + task_id, style="color:#e66")
        return P("Task cancelled: " + str(t.id), style="color:#4a4")

    @rt("/api/tasks", methods=["POST"])
    async def create_task(dot_id: str, goal: str):
        await runtime_submit(dot_id, goal)
        return RedirectResponse("/tasks", status_code=303)

    async def runtime_submit(dot_id, goal):
        task = tasks.create(goal, dot_id=dot_id)
        plan = planner.plan(goal)
        if not plan:
            tasks.set_status(task.id, "FAILED",
                             "Planner returned no steps")
            return task
        tasks.set_plan(task.id, plan)
        tasks.set_status(task.id, "PLANNING")
        tasks.set_status(task.id, "RUNNING")
        tasks.set_status(task.id, "COMPLETED",
                         "Plan created; awaiting configured "
                         "model/tool execution.")
        return task

    # ---- approvals ---------------------------------------------------------

    def _pending_cards():
        cards = []
        for a in approvals.pending():
            rows = ("<div style='border:1px solid #ccc;"
                    "padding:10px;margin:8px 0'>")
            rows += ("<h3>" + str(a.tool) + " · " + str(a.action)
                     + "</h3>")
            rows += "<p>" + str(a.reason or "") + "</p>"
            rows += ("<form action='/api/approvals/" + str(a.id)
                     + "/approve' method='post' "
                     "style='display:inline'>")
            rows += "<button>Approve once</button></form> "
            rows += ("<form action='/api/approvals/" + str(a.id)
                     + "/always' method='post' "
                     "style='display:inline'>")
            rows += "<button>Always allow this</button></form> "
            rows += ("<form action='/api/approvals/" + str(a.id)
                     + "/reject' method='post' "
                     "style='display:inline'>")
            rows += "<button>Reject</button></form></div>"
            cards.append(rows)
        return cards

    def _grants_table():
        grants = grants_store.list_grants()
        if not grants:
            return P("No always-allow rules granted yet.")
        rows = ""
        for tool, action in grants:
            rows += ("<tr><td>" + tool + "</td><td>"
                     + action.replace("<", "&lt;") + "</td><td>"
                     + '<form hx_post="/api/grants/revoke" '
                       'hx_target="#grants-result" '
                       'hx_swap="innerHTML">'
                     + '<input type="hidden" name="tool" value="' + tool
                     + '"><input type="hidden" name="action" value="'
                     + action.replace('"', "&quot;") + '">'
                     + "<button>Revoke</button></form></td></tr>")
        return Div(
            Table(Thead(Th("Tool"), Th("Action"), Th("")),
                  Tr(Td(raw(rows)))),
            P(Small("Revoking takes effect immediately and is "
                    "audited.")))

    @rt("/approvals")
    def approval_page():
        return Titled("Approvals", H1("Approval Center"),
                      H2("Pending"),
                      Div(id="approvals-live",
                          hx_get="/api/approvals/pending",
                          hx_trigger="load, every 5s",
                          hx_swap="innerHTML"),
                      H2("Always-allow rules (persisted)"),
                      Div(_grants_table(), id="grants-result"))

    @rt("/api/approvals/pending")
    def approvals_pending_fragment():
        cards = _pending_cards()
        if not cards:
            return P("No pending approvals.")
        return raw("".join(cards))

    @rt("/api/approvals/{approval_id}/approve", methods=["POST"])
    def approve(approval_id: str):
        approvals.decide(approval_id, True)
        return RedirectResponse("/approvals", status_code=303)

    @rt("/api/approvals/{approval_id}/always", methods=["POST"])
    def always_allow(approval_id: str):
        approvals.decide(approval_id, True, always=True)
        return RedirectResponse("/approvals", status_code=303)

    @rt("/api/approvals/{approval_id}/reject", methods=["POST"])
    def reject(approval_id: str):
        approvals.decide(approval_id, False)
        return RedirectResponse("/approvals", status_code=303)

    @rt("/api/grants/revoke", methods=["POST"])
    def revoke_grant(tool: str, action: str):
        from nexora.control.audit import audit
        ok = grants_store.revoke_grant(tool, action)
        audit("user", tool=tool, action=action, decision="REVOKE",
              outcome="always-allow rule revoked" if ok
              else "always-allow rule not found")
        if not ok:
            return P("Rule not found: " + tool + " · "
                     + action.replace("<", "&lt;"),
                     style="color:#e66")
        return P("Revoked: " + tool + " · "
                 + action.replace("<", "&lt;") + ". "
                 "Future requests will ask again.",
                 style="color:#4a4")

    @rt("/settings")
    def settings_page():
        active = get_profile().name
        rows = "".join(
            "<tr><td><b>" + name + "</b>"
            + (" (active)" if name == active else "") + "</td>"
            + "<td>" + str(p.max_workers) + "</td><td>"
            + str(p.poll_seconds) + "s</td>"
            + "<td>" + ("yes" if p.allow_browser else "no") + "</td>"
            + "<td>" + str(p.context) + "</td></tr>"
            for name, p in PROFILES.items())
        return Titled("Settings", H1("Settings"),
                      H2("Device Profile"),
                      Table(Thead(Th("Profile"), Th("Max workers"),
                                  Th("Poll"), Th("Browser"),
                                  Th("Context")),
                            Tr(Td(raw(rows)))),
                      P("Set with NEXORA_PROFILE env var or: "
                        "nexora start --profile <name>"),
                      H2("System"),
                      P("Local-only: " + str(settings.local_only)),
                      P("Auth enabled: " + str(settings.auth_enabled)),
                      P("Host: " + str(settings.host) + ":"
                        + str(settings.port)),
                      Form(Button("Logout"), action="/auth/logout",
                           method="post"))

    app = AuthMiddleware(app)
    return app
