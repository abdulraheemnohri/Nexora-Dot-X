"""Central authentication service for Nexora web, API, and WebSocket access.

Sessions are process-global by design so middleware, route handlers, and
WebSocket handlers validate the same login token. API tokens remain compatible
with the existing environment-based deployment.
"""
import hashlib
import hmac
import os
import secrets
import time
from typing import Any


class AuthManager:
    SESSION_TTL = 60 * 60 * 12
    _sessions: dict[str, float] = {}

    def __init__(self, password_hash_env: str = "NEXORA_SECRET_PASSWORD_HASH"):
        self.password_hash_env = password_hash_env

    @staticmethod
    def hash_password(password: str, salt: str | None = None) -> str:
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100_000
        ).hex()
        return salt + "$" + digest

    @staticmethod
    def verify_password(password: str, stored: str) -> bool:
        try:
            salt, digest = stored.split("$", 1)
        except ValueError:
            return False
        check = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100_000
        ).hex()
        return hmac.compare_digest(check, digest)

    def login(self, password: str) -> str | None:
        stored = os.getenv(self.password_hash_env, "")
        if not stored or not self.verify_password(password, stored):
            return None
        token = secrets.token_urlsafe(32)
        self._sessions[token] = time.time() + self.SESSION_TTL
        return token

    def valid_session(self, token: str) -> bool:
        if not token:
            return False
        exp = self._sessions.get(token)
        if exp is None:
            return False
        if time.time() > exp:
            self._sessions.pop(token, None)
            return False
        return True

    def logout(self, token: str) -> None:
        self._sessions.pop(token, None)

    def authenticate(self, *, session: str = "", bearer: str = "") -> bool:
        return self.valid_session(session) or self.valid_api_token(bearer)

    @staticmethod
    def issue_api_token() -> str:
        return "nx_" + secrets.token_urlsafe(32)

    @staticmethod
    def valid_api_token(provided: str) -> bool:
        expected = os.getenv("NEXORA_SECRET_API_TOKEN", "")
        return bool(expected) and bool(provided) and hmac.compare_digest(
            provided, expected
        )

    @classmethod
    def clear_sessions(cls) -> None:
        cls._sessions.clear()
