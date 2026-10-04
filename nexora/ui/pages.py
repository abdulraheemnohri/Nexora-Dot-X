from fasthtml.common import *
from nexora.ui.app import shell

def dashboard(status): return shell("Nexora Dot X",H1("Nexora Dot X"),P("System 1 Control Center"),Div(Class="grid")(Div(Class="card")(H3("Runtime"),P(status["status"])),Div(Class="card")(H3("Local-only"),P(str(status["local_only"]))),Div(Class="card")(H3("Policy"),P("ALLOW / ASK / BLOCK"))))
def dots(items):
    cards=[Div(Class="card")(H3(d.name),P(d.mission or "No mission"),Span("ACTIVE" if d.enabled else "PAUSED",Class="badge")) for d in items]
    return shell("Dots",H1("Dots"),Div(*cards,Class="grid"))
def approvals(items):
    cards=[Div(Class="card")(H3(a.tool+" · "+a.action),P(a.reason),P("Risk: "+a.risk),P("ID: "+a.id)) for a in items]
    return shell("Approvals",H1("Approval Center"),*(cards or [P("No pending approvals.")]))
