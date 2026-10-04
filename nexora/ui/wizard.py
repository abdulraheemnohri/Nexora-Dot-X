"""First-run wizard: 6 steps, fully functional forms."""
from fasthtml.common import *
from starlette.responses import RedirectResponse

from nexora.config import settings
from nexora.bots.manager import BotManager
from nexora.bots.templates import TEMPLATES


def wizard_page(step: int = 1):
    steps = {
        1: ("Welcome",
            P("Nexora Dot X - your self-hosted autonomous AI OS. "
              "This wizard gets you from zero to your first Dot."),
            P("Storage, models and memory all stay on this machine.")),
        2: ("Mode",
            P("Local-only: " + str(settings.local_only)),
            P("LOCAL_ONLY=true means no remote inference, telemetry or uploads. "
              "Change via NEXORA_LOCAL_ONLY in .env")),
        3: ("Model setup",
            P("Model dir: " + str(settings.model_dir)),
            P("Drop .litertlm models into models/litert/, or run: "
              "pip install nexora-dot-x[litert]")),
        4: ("Workspace",
            P("Workspaces: " + str(settings.workspace_dir)),
            P("Each Dot gets an isolated workspace directory.")),
        5: ("Create first Dot", _first_dot_form()),
        6: ("Finish",
            P("Setup complete. Head to the Dashboard and queue your first task.")),
    }
    title, *body = steps.get(step, steps[1])
    nav = Div(*[A(str(i), href="/wizard?step=" + str(i),
                  cls="wz-step" + (" active" if i == step else ""))
                for i in range(1, 7)])
    nxt = "/wizard?step=" + str(step + 1) if step < 6 else "/"
    return Title("Nexora Dot X - Setup"), Main(
        H1("Nexora Dot X", cls="brand"),
        Section(H2("Step " + str(step) + "/6 - " + title), *body,
                A("Next" if step < 6 else "Dashboard", href=nxt, cls="btn"),
                nav, cls="card"))


def _first_dot_form():
    return Form(
        Select(*[Option(v["name"], value=k) for k, v in TEMPLATES.items()],
               name="template"),
        Input(name="name", placeholder="Or custom name"),
        Button("Create Dot", cls="btn"),
        action="/api/wizard/dot", method="post")


def create_first_dot(form) -> RedirectResponse:
    name = form.get("name") or ""
    template = form.get("template") or ""
    bots = BotManager()
    if name:
        bots.create(name=name)
    elif template in TEMPLATES:
        bots.create_from_template(template)
    return RedirectResponse("/wizard?step=6", status_code=303)
