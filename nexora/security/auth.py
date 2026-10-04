"""Configurable authentication: password hash + session tokens + API tokens.

For local single-user deployments auth can stay disabled
(NEXORA_AUTH_ENABLED=false); when enabled, every web session requires login
and API calls need a bearer token.
"""
import hashlib
import hmac
import os
import secrets
import time


class AuthManager:
    SESSION_TTL = 60 * 60 * 12  # 12h

    def __init__(self, password_hash_env: str = "NEXORA_SECRET_PASSWORD_HASH"):
        self._sessions: dict[str, float] = {}

    # ---- password handling ----

    @staticmethod
    def hash_password(password: str, salt: str | None = None) -> str:
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(),
                                     100_000).hex()
        return salt + "$" + digest

    @staticmethod
    def verify_password(password: str, stored: str) -> bool:
        try:
            salt, digest = stored.split("$", 1)
        except ValueError:
            return False
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(),
                                    100_000).hex()
        return hmac.compare_digest(check, digest)

    # ---- sessions ----

    def login(self, password: str) -> str | None:
        stored = os.getenv("NEXORA_SECRET_PASSWORD_HASH", "")
        if not stored or not self.verify_password(password, stored):
            return None
        token = secrets.token_urlsafe(32)
        self._sessions[token] = time.time() + self.SESSION_TTL
        return token

    def valid_session(self, token: str) -> bool:
        exp = self._sessions.get(token)
        if exp is None:
            return False
        if time.time() > exp:
            self._sessions.pop(token, None)
            return False
        return True

    def logout(self, token: str):
        self._sessions.pop(token, None)

    # ---- API tokens ----

    @staticmethod
    def issue_api_token() -> str:
        return "nx_" + secrets.token_urlsafe(32)

    @staticmethod
    def valid_api_token(provided: str) -> bool:
        expected = os.getenv("NEXORA_SECRET_API_TOKEN", "")
        return bool(expected) and hmac.compare_digest(provided, expected)
