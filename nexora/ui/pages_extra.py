from fasthtml.common import *
from nexora.ui.app import shell
def tasks(items):
    return shell("Tasks",H1("Tasks"),*(Div(Class="card")(H3(t.goal),P(f"{t.status} · {t.id}")) for t in items))
def memory(items):
    return shell("Memory",H1("Memory"),*(Div(Class="card")(P(m.content),Small(f"{m.memory_type} · confidence {m.confidence}")) for m in items))
