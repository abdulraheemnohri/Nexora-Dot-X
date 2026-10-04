"""ASGI middleware: enforce auth when NEXORA_AUTH_ENABLED=true.

Rules:
  - /login, static assets and the WebSocket handshake stay open
  - when enabled, every route requires a Bearer token OR a valid session
    cookie; pages without either redirect to /login
Auth disabled => middleware is a no-op.
"""
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from nexora.security.auth import AuthManager

COOKIE = "nexora_session"


class AuthMiddleware(BaseHTTPMiddleware):
    OPEN_PATHS = ("/login", "/auth/login", "/favicon.ico", "/static")

    def __init__(self, app):
        super().__init__(app)
        self.auth = AuthManager()

    async def dispatch(self, request, call_next):
        if os.getenv("NEXORA_AUTH_ENABLED", "false").lower() != "true":
            return await call_next(request)

        path = request.url.path
        if path.startswith(self.OPEN_PATHS):
            return await call_next(request)

        token = request.cookies.get(COOKIE, "")
        if token and self.auth.valid_session(token):
            return await call_next(request)

        bearer = (request.headers.get("authorization") or "")
        if bearer.startswith("Bearer "):
            bearer = bearer.removeprefix("Bearer ").strip()
            if bearer and self.auth.valid_api_token(bearer):
                return await call_next(request)

        if path.startswith("/api/"):
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        return RedirectResponse("/login", status_code=303)
