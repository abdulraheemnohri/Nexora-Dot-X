from nexora.security.auth import AuthManager


def test_password_roundtrip():
    h = AuthManager.hash_password("secret123")
    assert AuthManager.verify_password("secret123", h)
    assert not AuthManager.verify_password("wrong", h)


def test_session_lifecycle(monkeypatch):
    monkeypatch.setenv("NEXORA_SECRET_PASSWORD_HASH",
                       AuthManager.hash_password("pw"))
    am = AuthManager()
    token = am.login("pw")
    assert token is not None
    assert am.valid_session(token)
    am.logout(token)
    assert not am.valid_session(token)
    assert am.login("bad") is None
