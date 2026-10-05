"""HTTP authentication middleware.

WebSocket authentication is handled explicitly by the WebSocket endpoint
because Starlette HTTP middleware does not reliably gate upgraded sockets.
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

        session = request.cookies.get(COOKIE, "")
        bearer = (request.headers.get("authorization") or "")
        if bearer.startswith("Bearer "):
            bearer = bearer.removeprefix("Bearer ").strip()

        if self.auth.authenticate(session=session, bearer=bearer):
            return await call_next(request)

        if path.startswith("/api/"):
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        return RedirectResponse("/login", status_code=303)


def websocket_authenticated(websocket) -> bool:
    """Validate a WebSocket before accepting it."""
    if os.getenv("NEXORA_AUTH_ENABLED", "false").lower() != "true":
        return True
    session = websocket.cookies.get(COOKIE, "")
    bearer = websocket.query_params.get("token", "")
    header = websocket.headers.get("authorization", "")
    if not bearer and header.startswith("Bearer "):
        bearer = header.removeprefix("Bearer ").strip()
    return AuthManager().authenticate(session=session, bearer=bearer)
