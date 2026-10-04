import os

from starlette.testclient import TestClient

from nexora.security.middleware import AuthMiddleware


def _app():
    from fasthtml.common import fast_app
    app, rt = fast_app()

    @rt("/hello")
    def hello():
        return {"ok": True}

    @rt("/login")
    def login():
        return {"page": "login"}

    return AuthMiddleware(app)


def test_open_when_disabled():
    os.environ.pop("NEXORA_AUTH_ENABLED", None)
    client = TestClient(_app())
    assert client.get("/hello").status_code == 200


def test_redirects_when_enabled():
    os.environ["NEXORA_AUTH_ENABLED"] = "true"
    try:
        client = TestClient(_app())
        r = client.get("/hello", follow_redirects=False)
        assert r.status_code == 303
        assert "/login" in r.headers["location"]
        assert client.get("/login").status_code == 200
    finally:
        os.environ["NEXORA_AUTH_ENABLED"] = "false"


def test_api_requires_token_when_enabled():
    os.environ["NEXORA_AUTH_ENABLED"] = "true"
    os.environ["NEXORA_SECRET_API_TOKEN"] = "nx_test_token"
    try:
        client = TestClient(_app())
        blocked = client.get("/hello", follow_redirects=False)
        assert blocked.status_code == 303
        ok = client.get("/hello", headers={"Authorization": "Bearer nx_test_token"},
                        follow_redirects=False)
        assert ok.status_code == 200
    finally:
        os.environ["NEXORA_AUTH_ENABLED"] = "false"
        os.environ.pop("NEXORA_SECRET_API_TOKEN", None)
