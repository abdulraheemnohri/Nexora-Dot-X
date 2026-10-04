from fasthtml.common import *
from nexora.config import settings
from nexora.database.engine import engine
from nexora.database.repositories import init_db

def create_app():
    init_db(engine)
    app, rt = fast_app()

    @rt("/")
    def get():
        return Titled("Nexora Dot X",
            H1("Nexora Dot X"),
            P("Local-first autonomous AI control center"),
            A("Health", href="/api/status"),
        )

    @rt("/api/status")
    def status():
        return {"status": "ready", "local_only": settings.local_only}

    return app
