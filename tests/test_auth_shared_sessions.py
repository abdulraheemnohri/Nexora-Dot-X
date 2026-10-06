import os

from nexora.security.auth import AuthManager


def test_auth_sessions_are_shared(monkeypatch):
    password = "test-password"
    monkeypatch.setenv("NEXORA_SECRET_PASSWORD_HASH", AuthManager.hash_password(password))
    a = AuthManager()
    b = AuthManager()
    token = a.login(password)
    assert token
    assert b.valid_session(token)
    b.logout(token)
    assert not a.valid_session(token)


def test_api_token(monkeypatch):
    monkeypatch.setenv("NEXORA_SECRET_API_TOKEN", "nx_test")
    assert AuthManager.valid_api_token("nx_test")
    assert not AuthManager.valid_api_token("nx_other")
